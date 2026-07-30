from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEMD = ROOT / "systemd"
APACHE = ROOT / "apache"


def test_backup_service_is_operator_owned_and_hardened():
    text = (SYSTEMD / "seven-backup.service").read_text(encoding="utf-8")
    assert "Type=oneshot" in text
    assert "User=seven" in text
    assert "ExecStart=/opt/seven/venv/bin/python -m seven --backup" in text
    assert "EnvironmentFile=/etc/seven/seven-core.env" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "ReadWritePaths=/var/lib/seven" in text
    assert "AssertPathExists=/opt/seven/venv/bin/python" in text
    assert "AssertPathExists=/etc/seven/seven-core.env" in text
    assert "ConditionPathExists" not in text
    assert "seven-core.service" not in text
    assert "--restore-backup" not in text


def test_backup_timer_is_persistent_and_bounded():
    text = (SYSTEMD / "seven-backup.timer").read_text(encoding="utf-8")
    assert "OnCalendar=daily" in text
    assert "Persistent=true" in text
    assert "RandomizedDelaySec=30m" in text
    assert "Unit=seven-backup.service" in text


def test_public_mesh_route_reaches_only_the_separate_hmac_listener():
    text = (APACHE / "seven.conf").read_text(encoding="utf-8")
    assert "ProxyPass        /seven-mesh/ http://127.0.0.1:18766/" in text
    assert "<Location \"/seven-mesh/\">" in text
    assert "127.0.0.1:18765" in text  # documented as forbidden
    assert "ProxyPass        /seven-core/" not in text
    assert "ProxyPass        /ollama/" not in text
