"""Generate the tracked-file completion inventory deterministically."""
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "FILE_INVENTORY.csv"
GENERATED = {
    "docs/FILE_INVENTORY.csv",
    "docs/LEGACY_SYMBOL_INVENTORY.csv",
}

# Legacy capability sources whose useful behavior has a supported modern
# replacement. The archive stays import-inert so these files are evidence, not
# a second implementation.
RECOVERED_LEGACY_NAMES = {
    "action_item_digest.py", "auto_backup.py", "code_executor.py",
    "clipboard_assistant.py", "clipboard_history.py", "command_processor.py",
    "commands.py", "conversation_memory.py", "document_reader.py",
    "file_manager.py", "github_reader.py", "greeting_manager.py",
    "llm_provider.py", "memory.py", "music_player.py", "ollama.py",
    "ollama_manager.py", "opencode.py", "opencode_delegator.py",
    "plugin_loader.py", "robotics.py", "screen_capture.py", "screen_control.py",
    "self_scripting.py", "seven_mcp.py", "smart_reminders.py", "ssh_manager.py",
    "streaming_ollama.py", "system_monitor.py", "timer_system.py",
    "toast_notifications.py", "tool_library.py", "vision_system.py",
    "voice.py", "voice_engine.py", "web_scraper.py", "web_search.py",
    "window_awareness.py",
}

# Useful ideas that are deliberately outside the supported 4.4 product
# contract. Keeping these sources quarantined is not a claim that they work.
EXCLUDED_LEGACY_NAMES = {
    "ambient_listener.py", "api_explorer.py", "calendar.py",
    "code_snippet_manager.py", "conversation_analytics.py", "daily_digest.py",
    "database_manager.py", "email_checker.py", "habit_tracker.py",
    "irc_client.py", "learning_journal.py", "lora_trainer.py",
    "mood_tracker.py", "motivation_engine.py", "news_digest.py",
    "pdf_generator.py", "pomodoro_timer.py", "quote_of_the_day.py",
    "telegram_client.py", "text_summarizer.py", "translation.py",
    "weather_reporter.py", "whatsapp_client.py", "web_ui.py",
}

REJECTED_LEGACY_MARKERS = {
    "affective", "biological_life", "dream", "emotion", "homeostasis",
    "metacognition", "phase5", "personality_quirks", "sentience",
    "social_sim", "surprise_system", "theory_of_mind", "vulnerability",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return sorted(p.decode("utf-8") for p in result.stdout.split(b"\0") if p)


def classify(path: str) -> tuple[str, str, str]:
    parts = Path(path).parts
    top = parts[0]
    if top == "seven":
        return "production", "keep-audit", "Supported runtime; verify implementation and tests"
    if top == "tests":
        return "current-tests", "keep-expand", "Current evidence; expand coverage and split suites"
    if top == "docs":
        return "current-docs", "keep-reconcile", "Documentation must match current behavior"
    if top == "scripts":
        return "release-tools", "keep-audit", "Developer/release automation requires validation"
    if top == ".github":
        return "ci", "keep-audit", "CI/release automation requires validation"
    if top != "_legacy":
        return "root-surface", "keep-consolidate", "Public launch/package/project surface"

    rel = "/".join(parts[2:]) if len(parts) > 2 else path
    area = parts[2] if len(parts) > 2 else "legacy-root"
    name = Path(path).name.lower()
    if name in RECOVERED_LEGACY_NAMES:
        return f"legacy-{area}", "quarantined-recovered", "Useful behavior is superseded by supported seven/ code; legacy file is import-inert evidence"
    if name in EXCLUDED_LEGACY_NAMES:
        return f"legacy-{area}", "quarantined-excluded", "Reviewed idea is outside the supported 4.4 release contract or lacks provider/hardware evidence"
    stem = Path(path).stem.lower()
    if any(marker in stem for marker in REJECTED_LEGACY_MARKERS):
        return f"legacy-{area}", "quarantined-rejected", "Random/template/theatrical cognition claim rejected as production behavior"
    if area in {"data", "test_data"}:
        return f"legacy-{area}", "quarantined-migration-evidence", "Retained only for tested migration/fixture archaeology; never loaded automatically"
    if area in {"tests_old"}:
        return "legacy-tests", "quarantined-test-reference", "Historical tests are not release gates; current tests provide supported evidence"
    if area in {"docs_old"} or name.endswith(".md") or "audit" in name:
        return "legacy-documentation", "quarantined-history", "Historical claims are non-authoritative; current ledger and matrix supersede them"
    if name.endswith((".bat", ".ps1", ".vbs", ".sh")) or name.startswith(("install", "uninstall", "launch", "create_")):
        return "legacy-lifecycle", "quarantined-superseded", "Obsolete lifecycle surface superseded by pyproject, current CLI and verified lifecycle scripts"
    return f"legacy-{area}", "quarantined-reference", f"Reviewed legacy artifact retained only for archaeology ({rel})"


def main() -> int:
    rows = []
    for relative in tracked_files():
        if relative.replace("\\", "/") in GENERATED:
            continue
        absolute = ROOT / relative
        data = absolute.read_bytes()
        # Git normalizes text files to LF; inventory must be stable on Windows/Linux.
        if b"\0" not in data:
            data = data.replace(b"\r\n", b"\n")
        area, disposition, reason = classify(relative)
        rows.append({
            "path": relative.replace("\\", "/"),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "area": area,
            "disposition": disposition,
            "reason": reason,
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} tracked non-generated paths to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
