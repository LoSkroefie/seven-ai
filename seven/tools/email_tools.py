"""Credential-safe SMTP and IMAP tools.

Credentials are accepted only through process environment variables and never
as model tool arguments or persisted settings.
"""
from __future__ import annotations

from email.header import decode_header
from email.message import EmailMessage
from email.utils import getaddresses, parseaddr
import imaplib
import json
import os
import smtplib
import ssl

from seven.security.credentials import CredentialUnavailable, read_credential

MAX_RECIPIENTS = 50
MAX_BODY = 200_000


def _stored_password() -> str:
    path = os.getenv("SEVEN_EMAIL_CREDENTIAL_FILE", "").strip()
    if not path:
        return ""
    try:
        return read_credential(path)
    except (CredentialUnavailable, OSError, ValueError, json.JSONDecodeError):
        return ""


def _integer(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _settings() -> dict:
    stored_password = _stored_password()
    return {
        "smtp_host": os.getenv("SEVEN_SMTP_HOST", "").strip(),
        "smtp_port": _integer("SEVEN_SMTP_PORT", 587),
        "smtp_ssl": os.getenv("SEVEN_SMTP_SSL", "0") == "1",
        "smtp_starttls": os.getenv("SEVEN_SMTP_STARTTLS", "1") != "0",
        "smtp_user": os.getenv("SEVEN_SMTP_USER", "").strip(),
        "smtp_password": os.getenv("SEVEN_SMTP_PASSWORD", "") or stored_password,
        "from_address": os.getenv("SEVEN_EMAIL_FROM", "").strip(),
        "imap_host": os.getenv("SEVEN_IMAP_HOST", "").strip(),
        "imap_port": _integer("SEVEN_IMAP_PORT", 993),
        "imap_ssl": os.getenv("SEVEN_IMAP_SSL", "1") != "0",
        "imap_user": os.getenv("SEVEN_IMAP_USER", "").strip(),
        "imap_password": os.getenv("SEVEN_IMAP_PASSWORD", "") or stored_password,
        "credential_file_configured": bool(
            os.getenv("SEVEN_EMAIL_CREDENTIAL_FILE", "").strip()
        ),
    }


def email_status() -> str:
    cfg = _settings()
    return json.dumps(
        {
            "ok": True,
            "smtp": {
                "configured": bool(
                    cfg["smtp_host"]
                    and cfg["from_address"]
                    and (not cfg["smtp_user"] or cfg["smtp_password"])
                ),
                "host": cfg["smtp_host"] or None,
                "port": cfg["smtp_port"],
                "ssl": cfg["smtp_ssl"],
                "starttls": cfg["smtp_starttls"],
                "from_address": cfg["from_address"] or None,
                "credentials_present": bool(cfg["smtp_user"] and cfg["smtp_password"]),
            },
            "imap": {
                "configured": bool(
                    cfg["imap_host"] and cfg["imap_user"] and cfg["imap_password"]
                ),
                "host": cfg["imap_host"] or None,
                "port": cfg["imap_port"],
                "ssl": cfg["imap_ssl"],
                "credentials_present": bool(cfg["imap_user"] and cfg["imap_password"]),
            },
            "credential_storage": (
                "environment or Windows DPAPI current-user credential file"
            ),
            "credential_file_configured": cfg["credential_file_configured"],
        },
        indent=2,
    )


def _addresses(value: str, label: str) -> list[str]:
    parsed = []
    for _, address in getaddresses([str(value or "")]):
        address = address.strip()
        if not address or "@" not in address or any(char in address for char in "\r\n"):
            raise ValueError(f"invalid {label} email address")
        parsed.append(address)
    if not parsed and label == "to":
        raise ValueError("at least one recipient is required")
    return parsed


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> str:
    cfg = _settings()
    if not cfg["smtp_host"] or not cfg["from_address"]:
        return "ERROR: SMTP is not configured; see email_status"
    if cfg["smtp_user"] and not cfg["smtp_password"]:
        return "ERROR: SMTP username is configured without its environment password"
    try:
        recipients = _addresses(to, "to")
        cc_list = _addresses(cc, "cc") if str(cc or "").strip() else []
        bcc_list = _addresses(bcc, "bcc") if str(bcc or "").strip() else []
        all_recipients = recipients + cc_list + bcc_list
        if len(all_recipients) > MAX_RECIPIENTS:
            return f"ERROR: recipient count exceeds {MAX_RECIPIENTS}"
        subject = str(subject or "").strip()
        body = str(body or "")
        if not subject or len(subject) > 998 or any(char in subject for char in "\r\n"):
            return "ERROR: subject must contain 1-998 characters without newlines"
        if len(body) > MAX_BODY:
            return f"ERROR: body exceeds {MAX_BODY} characters"
        from_address = parseaddr(cfg["from_address"])[1]
        if not from_address or "@" not in from_address:
            return "ERROR: SEVEN_EMAIL_FROM is invalid"

        message = EmailMessage()
        message["From"] = cfg["from_address"]
        message["To"] = ", ".join(recipients)
        if cc_list:
            message["Cc"] = ", ".join(cc_list)
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()
        if cfg["smtp_ssl"]:
            client = smtplib.SMTP_SSL(
                cfg["smtp_host"], cfg["smtp_port"], timeout=30, context=context
            )
        else:
            client = smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30)
        with client:
            client.ehlo()
            if not cfg["smtp_ssl"] and cfg["smtp_starttls"]:
                client.starttls(context=context)
                client.ehlo()
            if cfg["smtp_user"]:
                client.login(cfg["smtp_user"], cfg["smtp_password"])
            refused = client.send_message(message, to_addrs=all_recipients)
        if refused:
            return json.dumps(
                {
                    "ok": False,
                    "error": "one or more recipients were refused",
                    "refused": sorted(refused),
                }
            )
        return json.dumps(
            {
                "ok": True,
                "sent": True,
                "recipients": all_recipients,
                "subject": subject,
            }
        )
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        return f"ERROR sending email: {exc}"


def _decode(value: str | None) -> str:
    output = []
    for part, charset in decode_header(value or ""):
        if isinstance(part, bytes):
            output.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            output.append(part)
    return "".join(output)


def list_recent_email(
    limit: int = 10,
    mailbox: str = "INBOX",
    unread_only: bool = True,
) -> str:
    cfg = _settings()
    if not cfg["imap_host"] or not cfg["imap_user"] or not cfg["imap_password"]:
        return "ERROR: IMAP is not configured; see email_status"
    mailbox = str(mailbox or "INBOX").strip()
    if (
        not mailbox
        or len(mailbox) > 200
        or any(ord(char) < 32 for char in mailbox)
        or any(char in mailbox for char in "\r\n")
    ):
        return "ERROR: invalid mailbox name"
    limit = max(1, min(int(limit), 100))
    client = None
    try:
        if cfg["imap_ssl"]:
            client = imaplib.IMAP4_SSL(
                cfg["imap_host"],
                cfg["imap_port"],
                ssl_context=ssl.create_default_context(),
                timeout=30,
            )
        else:
            client = imaplib.IMAP4(cfg["imap_host"], cfg["imap_port"], timeout=30)
        client.login(cfg["imap_user"], cfg["imap_password"])
        status, _ = client.select(mailbox, readonly=True)
        if status != "OK":
            return f"ERROR: could not open IMAP mailbox {mailbox}"
        status, data = client.search(None, "UNSEEN" if unread_only else "ALL")
        if status != "OK":
            return "ERROR: IMAP search failed"
        ids = (data[0] or b"").split()[-limit:]
        messages = []
        for message_id in reversed(ids):
            status, payload = client.fetch(
                message_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])"
            )
            if status != "OK" or not payload:
                continue
            raw = next(
                (
                    item[1]
                    for item in payload
                    if isinstance(item, tuple) and len(item) > 1
                ),
                b"",
            )
            from email.parser import BytesParser

            header = BytesParser().parsebytes(raw)
            messages.append(
                {
                    "id": message_id.decode("ascii", errors="replace"),
                    "from": _decode(header.get("From")),
                    "subject": _decode(header.get("Subject")),
                    "date": header.get("Date", ""),
                    "message_id": header.get("Message-ID", ""),
                }
            )
        return json.dumps(
            {
                "ok": True,
                "mailbox": mailbox,
                "unread_only": bool(unread_only),
                "count": len(messages),
                "messages": messages,
                "bodies_retained": False,
            },
            indent=2,
        )
    except (OSError, imaplib.IMAP4.error, ValueError) as exc:
        return f"ERROR listing email: {exc}"
    finally:
        if client is not None:
            try:
                client.logout()
            except (OSError, imaplib.IMAP4.error):
                pass


def register(reg) -> None:
    from seven.tools.registry import Tool

    reg.register(
        Tool(
            "email_status",
            "Report SMTP/IMAP readiness without exposing credentials.",
            {"type": "object", "properties": {}},
            email_status,
        )
    )
    reg.register(
        Tool(
            "send_email",
            "Send a plain-text email using operator-owned environment configuration.",
            {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "cc": {"type": "string"},
                    "bcc": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
            send_email,
        )
    )
    reg.register(
        Tool(
            "list_recent_email",
            "List bounded IMAP message headers; message bodies are not retained.",
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "mailbox": {"type": "string"},
                    "unread_only": {"type": "boolean"},
                },
            },
            list_recent_email,
        )
    )
