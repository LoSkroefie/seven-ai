from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEMD = ROOT / "systemd"


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
