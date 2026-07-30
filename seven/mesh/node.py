"""Lifecycle, LAN discovery, hub sync, and local inbox for Seven Mesh."""
from __future__ import annotations

import json
import logging
import platform
import secrets
import socket
import struct
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from seven import __version__, config
from seven.mesh.identity import NodeIdentity, load_or_create_identity
from seven.mesh.security import (
    MeshAuthError,
    sign_beacon,
    sign_request,
    validate_secret,
    verify_beacon,
)
from seven.mesh.server import MeshHTTPServer
from seven.mesh.store import MeshStore


logger = logging.getLogger("seven.mesh")


@dataclass
class MeshSettings:
    enabled: bool
    secret: str
    data_dir: Path
    node_name: str
    listen: bool = True
    listen_host: str = "127.0.0.1"
    listen_port: int = 18766
    advertise_url: str = ""
    hub_url: str = ""
    sync_seconds: float = 30.0
    online_seconds: int = 180
    max_skew_seconds: int = 120
    message_ttl_seconds: int = 86400
    request_timeout: float = 10.0
    lan_discovery: bool = False
    lan_group: str = "239.255.83.86"
    lan_port: int = 18767

    @classmethod
    def from_config(cls) -> "MeshSettings":
        return cls(
            enabled=bool(config.MESH_ENABLED),
            secret=str(config.MESH_SECRET),
            data_dir=Path(config.DATA_DIR),
            node_name=str(config.MESH_NODE_NAME),
            listen=bool(config.MESH_LISTEN),
            listen_host=str(config.MESH_LISTEN_HOST),
            listen_port=int(config.MESH_LISTEN_PORT),
            advertise_url=str(config.MESH_ADVERTISE_URL),
            hub_url=str(config.MESH_HUB_URL),
            sync_seconds=float(config.MESH_SYNC_SECONDS),
            online_seconds=int(config.MESH_ONLINE_SECONDS),
            max_skew_seconds=int(config.MESH_MAX_SKEW_SECONDS),
            message_ttl_seconds=int(config.MESH_MESSAGE_TTL_SECONDS),
            request_timeout=float(config.MESH_REQUEST_TIMEOUT),
            lan_discovery=bool(config.MESH_LAN_DISCOVERY),
            lan_group=str(config.MESH_LAN_GROUP),
            lan_port=int(config.MESH_LAN_PORT),
        )


class MeshClient:
    def __init__(
        self,
        base_url: str,
        *,
        secret: str,
        node_id: str,
        timeout: float,
    ):
        self.base_url = str(base_url).rstrip("/") + "/"
        self.secret = validate_secret(secret)
        self.node_id = node_id
        self.timeout = max(1.0, float(timeout))
        self.session = requests.Session()
        self.session.trust_env = False

    def request(self, method: str, route: str, payload: dict | None = None) -> dict:
        route = "/" + route.lstrip("/")
        raw = b""
        headers: dict[str, str] = {}
        if payload is not None:
            raw = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"
        headers.update(
            sign_request(
                self.secret,
                self.node_id,
                method,
                route,
                raw,
            )
        )
        response = self.session.request(
            method.upper(),
            urljoin(self.base_url, route.lstrip("/")),
            data=raw if payload is not None else None,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("Seven mesh peer returned an invalid response")
        return result


class LanDiscovery:
    def __init__(self, node: "MeshNode"):
        self.node = node
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket: socket.socket | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", self.node.settings.lan_port))
            membership = struct.pack(
                "=4sl",
                socket.inet_aton(self.node.settings.lan_group),
                socket.INADDR_ANY,
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            sock.settimeout(1.0)
        except Exception:
            sock.close()
            raise
        self._socket = sock
        self._thread = threading.Thread(
            target=self._run,
            name="seven-mesh-lan",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run(self) -> None:
        last_beacon = 0.0
        while not self._stop.is_set():
            now = time.monotonic()
            if now - last_beacon >= max(5.0, self.node.settings.sync_seconds):
                self._send_beacon()
                last_beacon = now
            sock = self._socket
            if sock is None:
                return
            try:
                raw, _address = sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                payload = json.loads(raw.decode("utf-8"))
                verified = verify_beacon(
                    self.node.settings.secret,
                    payload,
                    self.node.store.claim_nonce,
                    max_skew_seconds=self.node.settings.max_skew_seconds,
                )
                if verified["node_id"] == self.node.identity.node_id:
                    continue
                self.node.store.upsert_peer(verified, source="lan")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError, MeshAuthError):
                logger.debug("ignored invalid Seven LAN beacon", exc_info=True)

    def _send_beacon(self) -> None:
        sock = self._socket
        if sock is None:
            return
        payload = sign_beacon(
            self.node.settings.secret,
            {
                **self.node.presence(),
                "timestamp": int(time.time()),
                "nonce": secrets.token_urlsafe(18),
            },
        )
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            sock.sendto(
                raw,
                (self.node.settings.lan_group, self.node.settings.lan_port),
            )
        except OSError:
            logger.debug("Seven LAN beacon send failed", exc_info=True)


class MeshNode:
    def __init__(self, memory=None, settings: MeshSettings | None = None):
        self.memory = memory
        self.settings = settings or MeshSettings.from_config()
        self.identity: NodeIdentity | None = None
        self.store: MeshStore | None = None
        self.server: MeshHTTPServer | None = None
        self.discovery: LanDiscovery | None = None
        self._sync_stop = threading.Event()
        self._sync_wake = threading.Event()
        self._sync_thread: threading.Thread | None = None
        self._started = False
        self._error = ""
        if self.settings.enabled:
            try:
                validate_secret(self.settings.secret)
            except ValueError as exc:
                self._error = str(exc)
            else:
                self.identity = load_or_create_identity(self.settings.data_dir)
                self.store = MeshStore(self.settings.data_dir / "seven_mesh.db")

    @property
    def operational(self) -> bool:
        return bool(
            self.settings.enabled
            and not self._error
            and self.identity is not None
            and self.store is not None
        )

    def presence(self) -> dict[str, Any]:
        if self.identity is None:
            raise RuntimeError(self._error or "Seven Mesh is disabled")
        return {
            "node_id": self.identity.node_id,
            "name": self.settings.node_name,
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "endpoint": self.settings.advertise_url,
            "capabilities": ["presence", "messaging", "peer-registry"],
            "seven_version": __version__,
        }

    def start(self) -> bool:
        if self._started:
            return self.operational
        if not self.operational:
            if self.settings.enabled:
                logger.error("Seven Mesh disabled by invalid configuration: %s", self._error)
            return False
        self._started = True
        self._sync_stop.clear()
        self._sync_wake.clear()
        assert self.store is not None
        self.store.upsert_peer(self.presence(), source="self")
        try:
            if self.settings.listen:
                self.server = MeshHTTPServer(
                    (self.settings.listen_host, self.settings.listen_port),
                    secret=self.settings.secret,
                    store=self.store,
                    max_skew_seconds=self.settings.max_skew_seconds,
                    message_ttl_seconds=self.settings.message_ttl_seconds,
                )
                self.server.start()
            if self.settings.lan_discovery:
                self.discovery = LanDiscovery(self)
                self.discovery.start()
        except Exception as exc:
            self._error = f"mesh listener startup failed: {exc}"
            logger.exception(self._error)
            self.stop()
            return False
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            name="seven-mesh-sync",
            daemon=True,
        )
        self._sync_thread.start()
        logger.info(
            "Seven Mesh node=%s listen=%s hub=%s lan=%s",
            self.identity.node_id,
            bool(self.server),
            bool(self.settings.hub_url),
            bool(self.discovery),
        )
        return True

    def stop(self) -> None:
        self._sync_stop.set()
        self._sync_wake.set()
        if self.discovery is not None:
            self.discovery.stop()
            self.discovery = None
        if self.server is not None:
            self.server.stop()
            self.server = None
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)
        self._started = False

    def _client(self, base_url: str) -> MeshClient:
        if self.identity is None:
            raise RuntimeError(self._error or "Seven Mesh is disabled")
        return MeshClient(
            base_url,
            secret=self.settings.secret,
            node_id=self.identity.node_id,
            timeout=self.settings.request_timeout,
        )

    def _sync_loop(self) -> None:
        while not self._sync_stop.is_set():
            try:
                self.sync_once()
                self._error = ""
            except Exception as exc:
                self._error = f"mesh sync failed: {exc}"
                logger.warning(self._error)
            self._sync_wake.wait(max(5.0, self.settings.sync_seconds))
            self._sync_wake.clear()

    def sync_once(self) -> dict[str, Any]:
        if not self.operational or self.store is None or self.identity is None:
            raise RuntimeError(self._error or "Seven Mesh is disabled")
        self.store.upsert_peer(self.presence(), source="self")
        self._accept_messages(
            self.store.take_relay(self.identity.node_id, limit=50),
            source="local-relay",
        )
        result: dict[str, Any] = {"ok": True, "hub": False, "received": 0}
        if not self.settings.hub_url:
            return result
        client = self._client(self.settings.hub_url)
        presence = client.request("POST", "/v1/presence", self.presence())
        for peer in presence.get("peers") or []:
            if isinstance(peer, dict):
                self.store.upsert_peer(peer, source="hub")
        inbox = client.request("GET", "/v1/inbox")
        received = self._accept_messages(inbox.get("messages") or [], source="hub")
        return {"ok": True, "hub": True, "received": received}

    def _accept_messages(self, messages: list, *, source: str) -> int:
        if self.store is None or self.identity is None:
            return 0
        received = 0
        for message in messages:
            if not isinstance(message, dict):
                continue
            if str(message.get("target_node_id") or "") != self.identity.node_id:
                continue
            sender = str(message.get("sender_node_id") or "")
            if self.store.record_local(
                message,
                direction="in",
                peer_node_id=sender,
                status="unread",
            ):
                received += 1
                if self.memory is not None:
                    try:
                        self.memory.add_event(
                            "mesh_message_received",
                            sender,
                            source,
                            str(message.get("content") or "")[:1000],
                            {
                                "message_id": message.get("message_id"),
                                "kind": message.get("kind"),
                            },
                        )
                    except Exception:
                        logger.exception("failed to record Seven mesh event")
        return received

    def send(
        self,
        target_node_id: str,
        content: str,
        *,
        kind: str = "message",
        context: dict | None = None,
    ) -> dict:
        if not self.operational:
            raise RuntimeError(self._error or "Seven Mesh is disabled")
        assert self.store is not None
        assert self.identity is not None
        target = str(target_node_id).strip()
        text = str(content).strip()
        if not text:
            raise ValueError("message content is required")
        base_url = self.settings.hub_url
        if not base_url:
            peer = next(
                (
                    item
                    for item in self.store.peers(
                        online_seconds=self.settings.online_seconds
                    )
                    if item["node_id"] == target and item.get("endpoint")
                ),
                None,
            )
            base_url = str((peer or {}).get("endpoint") or "")
        if not base_url:
            raise RuntimeError("no reachable hub or peer endpoint is configured")
        response = self._client(base_url).request(
            "POST",
            "/v1/messages",
            {
                "target_node_id": target,
                "kind": str(kind)[:64],
                "content": text,
                "context": context or {},
            },
        )
        message = response["message"]
        self.store.record_local(
            message,
            direction="out",
            peer_node_id=target,
            status="queued",
        )
        return message

    def status(self) -> dict[str, Any]:
        peers = (
            self.store.peers(online_seconds=self.settings.online_seconds)
            if self.store is not None
            else []
        )
        unread = (
            self.store.local_messages(direction="in", unread_only=True, limit=200)
            if self.store is not None
            else []
        )
        return {
            "enabled": bool(self.settings.enabled),
            "operational": self.operational,
            "started": bool(self._started),
            "node_id": self.identity.node_id if self.identity is not None else "",
            "node_name": self.settings.node_name,
            "hub_configured": bool(self.settings.hub_url),
            "listener_active": bool(self.server),
            "lan_discovery_active": bool(self.discovery),
            "online_peers": sum(
                1
                for peer in peers
                if peer.get("online") and peer["node_id"] != self.identity.node_id
            ),
            "known_peers": max(
                0,
                sum(1 for peer in peers if peer["node_id"] != self.identity.node_id),
            ),
            "unread_messages": len(unread),
            "last_error": self._error,
            "store_integrity": (
                self.store.integrity_check()
                if self.store is not None
                else "not_initialized"
            ),
        }

    def peers(self, *, include_offline: bool = True) -> list[dict]:
        if self.store is None or self.identity is None:
            return []
        return [
            peer
            for peer in self.store.peers(
                online_seconds=self.settings.online_seconds,
                include_offline=include_offline,
            )
            if peer["node_id"] != self.identity.node_id
        ]

    def inbox(self, *, unread_only: bool = True, mark_read: bool = False) -> list[dict]:
        if self.store is None:
            return []
        messages = self.store.local_messages(
            direction="in",
            unread_only=unread_only,
            limit=100,
        )
        if mark_read:
            self.store.mark_read([message["message_id"] for message in messages])
        return messages
