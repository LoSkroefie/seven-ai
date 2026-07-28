from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


STATIC = Path(__file__).resolve().parents[1] / "static"


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        if tag in {"img", "script", "link"}:
            source = values.get("src") or values.get("href")
            if source:
                self.sources.append(str(source).split("?", 1)[0])


def test_owner_page_has_every_control_and_local_asset() -> None:
    parser = IdCollector()
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    parser.feed(html)

    required = {
        "login-panel",
        "chat-panel",
        "login-error",
        "chat-status",
        "status",
        "conversation",
        "login-form",
        "password",
        "chat-form",
        "message",
        "send",
        "record",
        "camera",
        "voice",
        "logout",
        "camera-panel",
        "camera-preview",
        "camera-send",
        "camera-stop",
        "presence-line",
        "portrait-a",
        "portrait-b",
        "fullbody-avatar",
        "mind-state",
        "channel-state",
        "voice-state",
        "seven-space",
    }
    assert required <= parser.ids
    assert "https://" not in html
    assert "http://" not in html

    for source in parser.sources:
        if source.startswith(("data:", "#")):
            continue
        assert (STATIC / source).is_file(), source


def test_avatar_library_and_three_are_self_hosted() -> None:
    expected_assets = {
        "seven-amused.webp",
        "seven-blink.webp",
        "seven-concerned.webp",
        "seven-curious.webp",
        "seven-determined.webp",
        "seven-fullbody-idle.webp",
        "seven-fullbody-thinking.webp",
        "seven-fullbody-welcome.webp",
        "seven-listening.webp",
        "seven-ready.webp",
        "seven-speaking.webp",
        "seven-thinking.webp",
        "seven-welcoming.webp",
    }
    assert expected_assets <= {path.name for path in (STATIC / "assets").glob("*.webp")}
    vendor = STATIC / "vendor" / "three.module.min.js"
    assert vendor.stat().st_size > 600_000
    assert (STATIC / "vendor" / "three.LICENSE.txt").is_file()
    scene = (STATIC / "seven-scene.js").read_text(encoding="utf-8")
    assert 'from "./vendor/three.module.min.js"' in scene
    assert "cdn." not in scene


def test_client_tracks_only_current_page_turns_and_binds_media() -> None:
    client = (STATIC / "seven.js").read_text(encoding="utf-8")
    assert "pendingTurns.add(turnId)" in client
    assert "!pendingTurns.has(turnId)" in client
    assert 'addEventListener("turn_status"' in client
    assert 'api("api/media/audio"' in client
    assert 'api("api/media/jpeg"' in client
    assert "getUserMedia" in client
    assert "speechSynthesis" in client
    assert 'new CustomEvent("seven-state"' in client
    assert "Hi. I’m Seven. I’ve been waiting to meet you." in client
    assert "I could not complete that turn. The failure was recorded." not in client
