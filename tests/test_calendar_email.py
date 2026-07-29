import json

from seven.tools import calendar, email_tools


def test_local_calendar_round_trip_and_removal(tmp_path, monkeypatch):
    destination = tmp_path / "seven.ics"
    monkeypatch.setenv("SEVEN_CALENDAR_PATH", str(destination))

    created = json.loads(
        calendar.add_calendar_event(
            "Meet Seven",
            "2026-07-30T09:00:00+02:00",
            "2026-07-30T10:00:00+02:00",
            "Review memory, tools, and voice.",
            "Local machine",
            "meet-seven@local",
        )
    )
    assert created["ok"] is True
    assert destination.exists()
    assert b"BEGIN:VEVENT" in destination.read_bytes()

    listed = json.loads(calendar.list_calendar_events(limit=10))
    assert listed["count"] == 1
    assert listed["events"][0]["uid"] == "meet-seven@local"
    assert listed["events"][0]["start"] == "2026-07-30T07:00:00Z"
    assert "Review memory" in listed["events"][0]["description"]

    status = json.loads(calendar.calendar_status())
    assert status["events"] == 1
    assert status["cloud_sync"] is False

    removed = json.loads(calendar.remove_calendar_event("meet-seven@local"))
    assert removed == {"ok": True, "removed": "meet-seven@local", "remaining": 0}
    assert json.loads(calendar.list_calendar_events())["events"] == []


def test_calendar_rejects_invalid_ranges_and_duplicate_uids(tmp_path, monkeypatch):
    monkeypatch.setenv("SEVEN_CALENDAR_PATH", str(tmp_path / "seven.ics"))
    assert calendar.add_calendar_event(
        "Bad", "2026-07-30T10:00:00Z", "2026-07-30T09:00:00Z"
    ).startswith("ERROR: end")
    first = calendar.add_calendar_event(
        "One",
        "2026-07-30T09:00:00Z",
        "2026-07-30T10:00:00Z",
        uid="one@local",
    )
    assert json.loads(first)["ok"] is True
    assert "already exists" in calendar.add_calendar_event(
        "Again",
        "2026-07-31T09:00:00Z",
        "2026-07-31T10:00:00Z",
        uid="one@local",
    )


class _FakeSMTP:
    sent = None

    def __init__(self, host, port, timeout=0, context=None):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def ehlo(self):
        return 250

    def starttls(self, context=None):
        return 220

    def login(self, user, password):
        assert user == "seven@example.com"
        assert password == "environment-secret"

    def send_message(self, message, to_addrs):
        type(self).sent = (message, to_addrs)
        return {}


def test_email_status_redacts_credentials_and_send_uses_environment(monkeypatch):
    monkeypatch.setenv("SEVEN_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SEVEN_SMTP_USER", "seven@example.com")
    monkeypatch.setenv("SEVEN_SMTP_PASSWORD", "environment-secret")
    monkeypatch.setenv("SEVEN_EMAIL_FROM", "Seven <seven@example.com>")
    monkeypatch.setattr(email_tools.smtplib, "SMTP", _FakeSMTP)

    status = email_tools.email_status()
    assert "environment-secret" not in status
    assert json.loads(status)["smtp"]["configured"] is True

    result = json.loads(
        email_tools.send_email(
            "owner@example.com",
            "Seven is ready",
            "The local instance is healthy.",
            cc="audit@example.com",
        )
    )
    assert result["ok"] is True
    message, recipients = _FakeSMTP.sent
    assert recipients == ["owner@example.com", "audit@example.com"]
    assert message["Subject"] == "Seven is ready"
    assert "local instance is healthy" in message.get_content()


def test_email_rejects_unconfigured_and_header_injection(monkeypatch):
    for key in (
        "SEVEN_SMTP_HOST",
        "SEVEN_SMTP_USER",
        "SEVEN_SMTP_PASSWORD",
        "SEVEN_EMAIL_FROM",
    ):
        monkeypatch.delenv(key, raising=False)
    assert email_tools.send_email("a@example.com", "Subject", "Body").startswith(
        "ERROR: SMTP is not configured"
    )

    monkeypatch.setenv("SEVEN_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SEVEN_EMAIL_FROM", "seven@example.com")
    assert "without newlines" in email_tools.send_email(
        "a@example.com", "Subject\nBcc: victim@example.com", "Body"
    )


def test_email_uses_os_protected_credential_file(monkeypatch, tmp_path):
    credential = tmp_path / "email-credential.json"
    credential.write_text("encrypted-placeholder", encoding="utf-8")
    monkeypatch.setenv("SEVEN_EMAIL_CREDENTIAL_FILE", str(credential))
    monkeypatch.setenv("SEVEN_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SEVEN_SMTP_USER", "seven@example.com")
    monkeypatch.setenv("SEVEN_EMAIL_FROM", "seven@example.com")
    monkeypatch.delenv("SEVEN_SMTP_PASSWORD", raising=False)
    monkeypatch.setattr(
        email_tools, "read_credential", lambda path: "environment-secret"
    )
    monkeypatch.setattr(email_tools.smtplib, "SMTP", _FakeSMTP)

    status = json.loads(email_tools.email_status())
    assert status["smtp"]["configured"] is True
    assert status["credential_file_configured"] is True
    assert "environment-secret" not in json.dumps(status)
    result = json.loads(
        email_tools.send_email(
            "owner@example.com",
            "Secure credential",
            "Credential came from the operating-system protected store.",
        )
    )
    assert result["ok"] is True
