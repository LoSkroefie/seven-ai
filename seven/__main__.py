"""python -m seven"""
from __future__ import annotations

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from seven import config, __version__


def setup_logging():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                config.LOG_PATH,
                maxBytes=max(1024, config.LOG_MAX_BYTES),
                backupCount=max(1, config.LOG_BACKUP_COUNT),
                encoding="utf-8",
            ),
        ],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=f"Seven Real {__version__} — talk, listen, free will"
    )
    parser.add_argument(
        "--talk",
        action="store_true",
        help="PRIMARY: companion mode (voice or quiet text + free will)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Companion mode without mic/speakers (type; free will still on)",
    )
    parser.add_argument("--voice", action="store_true", help="CLI with voice extras")
    parser.add_argument("-c", "--command", type=str, help="One message and exit (power user)")
    parser.add_argument("--status", action="store_true", help="Health dump and exit")
    parser.add_argument("--provider", type=str, help="ollama|openai|anthropic|compat")
    parser.add_argument("--model", type=str, help="Override model name")
    parser.add_argument("--gui", action="store_true", help="Desktop chat (optional; prefer --talk)")
    parser.add_argument("--cli", action="store_true", help="Text CLI (power user)")
    parser.add_argument("--api", action="store_true", help="Start local REST API")
    parser.add_argument("--api-only", action="store_true", help="API only")
    parser.add_argument("--tier", choices=("core", "full"), help="Tool schema tier")
    parser.add_argument("--daemon", action="store_true", help="Always-on background Seven")
    parser.add_argument("--daemon-stop", action="store_true", help="Stop daemon")
    parser.add_argument("--daemon-status", action="store_true", help="Daemon status")
    parser.add_argument("--daemon-restart", action="store_true", help="Stop the owned daemon, then run it again")
    parser.add_argument("--backup", action="store_true", help="Create and verify a data backup")
    parser.add_argument("--verify-backup", type=str, metavar="ZIP", help="Verify a Seven backup")
    parser.add_argument("--restore-backup", type=str, metavar="ZIP", help="Restore verified backup while Seven is stopped")
    parser.add_argument("--install-startup", action="store_true", help="Start talk mode after user login")
    parser.add_argument("--install-startup-quiet", action="store_true", help="Start quiet companion mode after login")
    parser.add_argument("--remove-startup", action="store_true", help="Remove Seven's login startup entry")
    parser.add_argument("--startup-status", action="store_true", help="Show login startup status")
    parser.add_argument("--memory-check", action="store_true", help="Run SQLite integrity and memory statistics checks")
    parser.add_argument("--export-memory", type=str, metavar="JSON", help="Export portable memory JSON (audit excluded)")
    parser.add_argument("--export-memory-with-audit", type=str, metavar="JSON", help="Export memory JSON including redacted audit history")
    parser.add_argument("--migrate-legacy-memory", type=str, metavar="DB", help="Dry-run a v3 conversation-memory import")
    parser.add_argument("--apply-legacy-memory", type=str, metavar="DB", help="Back up and apply a v3 conversation-memory import")
    parser.add_argument("--memory-retention", type=int, metavar="DAYS", help="Dry-run bounded ephemeral-memory retention")
    parser.add_argument("--apply-memory-retention", type=int, metavar="DAYS", help="Back up and apply ephemeral-memory retention")
    parser.add_argument("--retention-scope", type=str, help="Comma-separated retention scopes; defaults to all supported ephemeral scopes")
    parser.add_argument(
        "--no-freewill",
        action="store_true",
        help="Disable free will (not recommended)",
    )
    args = parser.parse_args(argv)

    maintenance_actions = sum(bool(value) for value in (
        args.migrate_legacy_memory,
        args.apply_legacy_memory,
        args.memory_retention is not None,
        args.apply_memory_retention is not None,
    ))
    if maintenance_actions > 1:
        parser.error("select only one legacy-migration or memory-retention action")
    if args.retention_scope and args.memory_retention is None and args.apply_memory_retention is None:
        parser.error("--retention-scope requires a memory-retention action")

    setup_logging()

    if args.provider:
        config.LLM_PROVIDER = args.provider
    if args.model:
        config.OLLAMA_MODEL = args.model
    if args.tier:
        config.TOOL_TIER = args.tier
    if args.voice or (args.talk and not args.quiet):
        config.ENABLE_VOICE = True
    if args.quiet:
        config.ENABLE_VOICE = False
        os.environ["SEVEN_QUIET"] = "1"
    if args.api:
        config.ENABLE_API = True
    if args.no_freewill:
        config.ENABLE_FREEWILL = False

    if args.daemon_stop:
        from seven.runtime.daemon import stop_daemon
        return stop_daemon()

    if args.daemon_status:
        from seven.runtime.daemon import daemon_status
        print(daemon_status())
        return 0

    if args.daemon_restart:
        from seven.runtime.daemon import restart_daemon
        return restart_daemon(enable_api=args.api or config.ENABLE_API)

    if args.backup or args.verify_backup or args.restore_backup:
        import json
        from seven.runtime.backup import create_backup, restore_backup, verify_backup
        if args.backup:
            result = create_backup()
        elif args.verify_backup:
            result = verify_backup(Path(args.verify_backup))
        else:
            result = restore_backup(Path(args.restore_backup))
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("ok") else 1

    if args.install_startup or args.install_startup_quiet or args.remove_startup or args.startup_status:
        import json
        from seven.runtime.startup import install_startup, remove_startup, startup_status
        if args.install_startup or args.install_startup_quiet:
            result = install_startup(quiet=args.install_startup_quiet)
        elif args.remove_startup:
            result = remove_startup()
        else:
            result = startup_status()
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.memory_check or args.export_memory or args.export_memory_with_audit:
        import json
        from seven.runtime.memory_ops import export_memory, memory_check
        if args.memory_check:
            result = memory_check()
        else:
            destination = args.export_memory or args.export_memory_with_audit
            result = export_memory(Path(destination), include_audit=bool(args.export_memory_with_audit))
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.migrate_legacy_memory or args.apply_legacy_memory or args.memory_retention is not None or args.apply_memory_retention is not None:
        import json
        from seven.runtime.memory_maintenance import DEFAULT_RETENTION_SCOPE, apply_retention, migrate_legacy_memory
        try:
            if args.migrate_legacy_memory or args.apply_legacy_memory:
                source = args.migrate_legacy_memory or args.apply_legacy_memory
                result = migrate_legacy_memory(Path(source), apply=bool(args.apply_legacy_memory))
            else:
                days = args.memory_retention if args.memory_retention is not None else args.apply_memory_retention
                scopes = tuple(item.strip() for item in (args.retention_scope or "").split(",") if item.strip()) or DEFAULT_RETENTION_SCOPE
                result = apply_retention(days, scopes=scopes, apply=args.apply_memory_retention is not None)
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("ok") else 1
        except (OSError, ValueError, RuntimeError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            return 1

    if args.daemon:
        from seven.runtime.daemon import run_daemon
        return run_daemon(enable_api=args.api or config.ENABLE_API)

    from seven.agent.loop import Seven

    if args.status:
        s = Seven()
        print(s.handle("/status"))
        return 0

    if args.command:
        s = Seven()
        print(s.handle(args.command))
        s.shutdown()
        return 0

    if args.api_only:
        from seven.ui.api_server import run_api_blocking
        return run_api_blocking()

    if args.gui:
        from seven.ui.desktop import run_desktop
        run_desktop(
            enable_api=args.api or config.ENABLE_API,
            enable_voice=True,
        )
        return 0

    # Power-user text CLI only if requested
    if args.cli:
        if args.api or config.ENABLE_API:
            from seven.ui.api_server import start_api_server
            agent = Seven()
            start_api_server(background=True, agent=agent)
            _run_cli_with_agent(agent, voice=args.voice)
            return 0
        from seven.ui.cli import run_cli
        run_cli(voice=args.voice)
        return 0

    # DEFAULT PRODUCT: companion talk (quiet if --quiet or SEVEN_QUIET=1)
    from seven.ui.talk import run_talk
    run_talk(quiet=bool(args.quiet or os.getenv("SEVEN_QUIET") == "1"))
    return 0


def _run_cli_with_agent(agent: Seven, voice: bool = False):
    """CLI loop reusing an existing Seven instance (shared with API)."""
    print("=" * 60)
    print(f"  {config.BOT_NAME} Real  —  CLI + API  —  L4")
    print(f"  API http://{config.API_HOST}:{config.API_PORT}")
    print("=" * 60)
    agent.start_heartbeat()
    voice_io = None
    if voice or config.ENABLE_VOICE:
        from seven.voice.io import VoiceIO
        voice_io = VoiceIO()
    try:
        while True:
            try:
                user = input(f"{config.USER_NAME}> ").strip()
            except EOFError:
                break
            if not user:
                continue
            reply = agent.handle(user)
            if reply == "__QUIT__":
                print("Goodbye.")
                break
            print(f"\n{config.BOT_NAME}> {reply}\n")
            if voice_io and voice_io.tts_ok and config.ENABLE_VOICE:
                speak = reply if len(reply) < 800 else reply[:800] + "…"
                voice_io.speak(speak)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        agent.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
