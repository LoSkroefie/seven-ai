from __future__ import annotations

import queue
import threading
import logging

from .store import GatewayStore
from .upstream import SevenUpstream, SevenUpstreamError

LOGGER = logging.getLogger("seven.gateway.turns")


class TurnService:
    def __init__(self, store: GatewayStore, upstream: SevenUpstream, queue_limit: int):
        self.store = store
        self.upstream = upstream
        self.queue: queue.Queue[int | None] = queue.Queue(maxsize=queue_limit)
        self.stop_event = threading.Event()
        self.activity_condition = threading.Condition()
        self.worker = threading.Thread(target=self._run, name="seven-web-turns", daemon=True)
        self.worker.start()

    def enqueue(self, session_hash: str, message: str) -> int:
        turn_id = self.store.create_turn(session_hash, message)
        try:
            self.queue.put_nowait(turn_id)
        except queue.Full:
            self.store.update_turn(turn_id, "rejected", error_code="queue_full")
            raise
        self.notify_activity()
        return turn_id

    def notify_activity(self) -> None:
        with self.activity_condition:
            self.activity_condition.notify_all()

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                turn_id = self.queue.get(timeout=0.25)
            except queue.Empty:
                continue
            if turn_id is None:
                self.queue.task_done()
                break
            try:
                turn = self.store.get_turn_for_worker(turn_id)
                if not turn or turn["status"] != "queued":
                    continue
                self.store.update_turn(turn_id, "running")
                self.notify_activity()
                try:
                    reply = self.upstream.chat(turn["message"])
                except SevenUpstreamError as exc:
                    self.store.update_turn(turn_id, "failed", error_code=str(exc))
                except Exception as exc:
                    # Report the failure class without rendering its potentially
                    # secret-bearing message into logs, activity, or HTTP.
                    LOGGER.error("unexpected upstream failure type=%s", type(exc).__name__)
                    self.store.update_turn(
                        turn_id, "failed", error_code="seven_internal_failure"
                    )
                else:
                    self.store.update_turn(turn_id, "complete", reply=reply)
                self.notify_activity()
            finally:
                self.queue.task_done()

    def close(self) -> None:
        self.stop_event.set()
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
        self.worker.join(timeout=3)
