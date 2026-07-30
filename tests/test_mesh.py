from __future__ import annotations

import concurrent.futures
import json
import time

import pytest
import requests

from seven.mesh.identity import load_or_create_identity
from seven.mesh.node import MeshClient, MeshNode, MeshSettings
from seven.mesh.security import MeshAuthError, sign_request, verify_request
from seven.mesh.server import MeshHTTPServer
from seven.mesh.store import MeshStore
from seven.tools import mesh as mesh_tools
from seven.tools.registry import ToolRegistry


SECRET = "mesh-test-secret-" + ("x" * 40)


def _settings(path, name, **overrides):
    values = {
        "enabled": True,
        "secret": SECRET,
        "data_dir": path,
        "node_name": name,
        "listen": False,
        "sync_seconds": 3600,
        "lan_discovery": False,
        "request_timeout": 3,
    }
    values.update(overrides)
    return MeshSettings(**values)


def test_identity_is_private_stable_and_concurrent(tmp_path):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        identities = list(
            pool.map(lambda _index: load_or_create_identity(tmp_path), range(24))
        )
    assert len({item.node_id for item in identities}) == 1
    persisted = json.loads((tmp_path / "mesh_identity.json").read_text("utf-8"))
    assert persisted["node_id"] == identities[0].node_id
    assert not (tmp_path / ".mesh_identity.json.lock").exists()


def test_request_auth_rejects_tampering_expiry_and_replay(tmp_path):
    store = MeshStore(tmp_path / "mesh.db")
    node_id = "a" * 32
    body = b'{"hello":"mesh"}'
    headers = sign_request(
        SECRET,
        node_id,
        "POST",
        "/v1/presence",
        body,
        timestamp=1_000,
        nonce="fixed_nonce_value_123",
    )
    assert (
        verify_request(
            SECRET,
            headers,
            "POST",
            "/v1/presence",
            body,
            store.claim_nonce,
            now=1_000,
        )
        == node_id
    )
    with pytest.raises(MeshAuthError, match="replayed"):
        verify_request(
            SECRET,
            headers,
            "POST",
            "/v1/presence",
            body,
            store.claim_nonce,
            now=1_000,
        )
    fresh = sign_request(
        SECRET,
        node_id,
        "POST",
        "/v1/presence",
        body,
        timestamp=1_000,
        nonce="another_nonce_value_456",
    )
    with pytest.raises(MeshAuthError, match="signature"):
        verify_request(
            SECRET,
            fresh,
            "POST",
            "/v1/presence",
            b'{"hello":"tampered"}',
            store.claim_nonce,
            now=1_000,
        )
    expired = sign_request(
        SECRET,
        node_id,
        "GET",
        "/v1/peers",
        timestamp=100,
        nonce="expired_nonce_value_789",
    )
    with pytest.raises(MeshAuthError, match="timestamp"):
        verify_request(
            SECRET,
            expired,
            "GET",
            "/v1/peers",
            b"",
            store.claim_nonce,
            now=1_000,
        )


def test_two_nodes_discover_and_exchange_a_persistent_message(tmp_path):
    hub_store = MeshStore(tmp_path / "hub" / "mesh.db")
    hub = MeshHTTPServer(
        ("127.0.0.1", 0),
        secret=SECRET,
        store=hub_store,
    )
    hub.start()
    base = f"http://127.0.0.1:{hub.server_address[1]}"
    first = MeshNode(settings=_settings(tmp_path / "first", "Seven@first", hub_url=base))
    second = MeshNode(settings=_settings(tmp_path / "second", "Seven@second", hub_url=base))
    try:
        assert first.sync_once()["hub"] is True
        assert second.sync_once()["hub"] is True
        first.sync_once()
        assert [peer["node_id"] for peer in first.peers()] == [second.identity.node_id]

        queued = first.send(second.identity.node_id, "Hello from the first Seven.")
        assert queued["sender_node_id"] == first.identity.node_id
        assert second.sync_once()["received"] == 1
        inbox = second.inbox(unread_only=True)
        assert inbox[0]["content"] == "Hello from the first Seven."
        assert inbox[0]["peer_node_id"] == first.identity.node_id
        assert second.inbox(unread_only=True, mark_read=True)[0]["message_id"] == queued["message_id"]
        assert second.inbox(unread_only=True) == []
        assert second.store.integrity_check() == "ok"
    finally:
        hub.stop()


def test_mesh_http_requires_auth_and_does_not_offer_remote_execution(tmp_path):
    store = MeshStore(tmp_path / "hub.db")
    hub = MeshHTTPServer(("127.0.0.1", 0), secret=SECRET, store=store)
    hub.start()
    base = f"http://127.0.0.1:{hub.server_address[1]}"
    try:
        assert requests.get(base + "/health", timeout=3).status_code == 200
        assert requests.get(base + "/v1/peers", timeout=3).status_code == 401
        assert requests.post(base + "/v1/tools", json={}, timeout=3).status_code == 404
        identity = load_or_create_identity(tmp_path / "client")
        client = MeshClient(
            base,
            secret=SECRET,
            node_id=identity.node_id,
            timeout=3,
        )
        response = client.request(
            "POST",
            "/v1/presence",
            {
                "node_id": identity.node_id,
                "name": "Seven@test",
                "hostname": "test",
                "platform": "test",
                "endpoint": "",
                "capabilities": [],
            },
        )
        assert response["ok"] is True
    finally:
        hub.stop()


def test_mesh_tools_expose_status_peers_inbox_and_send(tmp_path):
    class Agent:
        mesh = MeshNode(settings=_settings(tmp_path, "Seven@tool-test"))

    registry = ToolRegistry(tier="lean")
    mesh_tools.register(registry, agent=Agent())
    assert {"mesh"}.issubset(registry.names())
    assert {
        "mesh_status",
        "mesh_peers",
        "mesh_inbox",
        "mesh_send",
    }.issubset(registry.all_names())
    status = json.loads(registry.execute("mesh", {"action": "status"}))
    assert status["operational"] is True
    failure = json.loads(
        registry.execute(
            "mesh",
            {
                "action": "send",
                "target_node_id": "b" * 32,
                "message": "hello",
            },
        )
    )
    assert failure["ok"] is False
    assert "reachable hub" in failure["error"]


def test_disabled_or_short_secret_never_opens_a_listener(tmp_path):
    disabled = MeshNode(
        settings=_settings(tmp_path / "disabled", "Seven@disabled", enabled=False)
    )
    assert disabled.start() is False
    assert disabled.status()["listener_active"] is False

    invalid = MeshNode(
        settings=_settings(
            tmp_path / "invalid",
            "Seven@invalid",
            secret="short",
            listen=True,
            listen_port=0,
        )
    )
    assert invalid.start() is False
    assert invalid.status()["operational"] is False
    assert "32 characters" in invalid.status()["last_error"]


def test_transient_sync_error_does_not_disable_valid_mesh(tmp_path):
    node = MeshNode(settings=_settings(tmp_path, "Seven@retry"))
    assert node.operational is True
    node._error = "mesh sync failed: temporary route error"
    assert node.operational is True
