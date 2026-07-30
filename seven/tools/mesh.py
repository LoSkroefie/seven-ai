"""Owner-authenticated communication between Seven installations."""
from __future__ import annotations

import json


def register(reg, agent=None):
    from seven.tools.registry import Tool

    def _mesh():
        mesh = getattr(agent, "mesh", None) if agent is not None else None
        if mesh is None:
            raise RuntimeError("Seven Mesh is unavailable in this process")
        return mesh

    def status() -> str:
        try:
            return json.dumps(_mesh().status(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    def peers(include_offline: bool = True) -> str:
        try:
            values = _mesh().peers(include_offline=bool(include_offline))
            return json.dumps(
                {"ok": True, "count": len(values), "peers": values},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    def inbox(unread_only: bool = True, mark_read: bool = False) -> str:
        try:
            values = _mesh().inbox(
                unread_only=bool(unread_only),
                mark_read=bool(mark_read),
            )
            return json.dumps(
                {"ok": True, "count": len(values), "messages": values},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    def send(
        target_node_id: str,
        message: str,
        kind: str = "message",
    ) -> str:
        try:
            sent = _mesh().send(
                target_node_id=target_node_id,
                content=message,
                kind=kind,
            )
            return json.dumps({"ok": True, "message": sent}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    def dispatch(
        action: str = "status",
        target_node_id: str = "",
        message: str = "",
        kind: str = "message",
        include_offline: bool = True,
        unread_only: bool = True,
        mark_read: bool = False,
    ) -> str:
        selected = str(action or "status").strip().lower()
        if selected == "status":
            return status()
        if selected == "peers":
            return peers(include_offline=include_offline)
        if selected == "inbox":
            return inbox(unread_only=unread_only, mark_read=mark_read)
        if selected == "send":
            return send(
                target_node_id=target_node_id,
                message=message,
                kind=kind,
            )
        return json.dumps(
            {
                "ok": False,
                "error": "action must be status, peers, inbox, or send",
            },
            ensure_ascii=False,
        )

    reg.register(
        Tool(
            name="mesh",
            description=(
                "Use Seven Mesh: inspect status, list authenticated Seven peers, "
                "read the inbox, or send a non-executable text message. Select one "
                "action: status, peers, inbox, or send."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "peers", "inbox", "send"],
                    },
                    "target_node_id": {"type": "string"},
                    "message": {"type": "string"},
                    "kind": {"type": "string"},
                    "include_offline": {"type": "boolean"},
                    "unread_only": {"type": "boolean"},
                    "mark_read": {"type": "boolean"},
                },
            },
            handler=dispatch,
        )
    )
    reg.register(
        Tool(
            name="mesh_status",
            description=(
                "Inspect this Seven installation's stable mesh identity, connectivity, "
                "peer counts, unread message count, and last transport error."
            ),
            parameters={"type": "object", "properties": {}},
            handler=status,
        )
    )
    reg.register(
        Tool(
            name="mesh_peers",
            description=(
                "List authenticated Seven installations known through LAN discovery "
                "or the configured rendezvous hub. Use before sending a mesh message."
            ),
            parameters={
                "type": "object",
                "properties": {"include_offline": {"type": "boolean"}},
            },
            handler=peers,
        )
    )
    reg.register(
        Tool(
            name="mesh_inbox",
            description=(
                "Read messages sent by other authenticated Seven installations. "
                "Messages are communication only and never execute tools automatically."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "unread_only": {"type": "boolean"},
                    "mark_read": {"type": "boolean"},
                },
            },
            handler=inbox,
        )
    )
    reg.register(
        Tool(
            name="mesh_send",
            description=(
                "Send a text message to an authenticated Seven peer by exact node ID. "
                "This queues communication; it does not remotely execute commands."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "target_node_id": {"type": "string"},
                    "message": {"type": "string"},
                    "kind": {"type": "string"},
                },
                "required": ["target_node_id", "message"],
            },
            handler=send,
        )
    )
