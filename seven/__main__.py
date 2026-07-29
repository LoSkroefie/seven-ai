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

from seven import __version__
from seven.setup_wizard import apply_saved_environment

_SETUP_SETTINGS_ERROR = None


class _LazyConfig:
    """Keep setup dry-runs side-effect free while preserving module API."""

    def __init__(self):
        object.__setattr__(self, "_module", None)

    def _load(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            from seven import config as runtime_config

            module = runtime_config
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __setattr__(self, name, value):
        setattr(self._load(), name, value)


config = _LazyConfig()


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
    global config, _SETUP_SETTINGS_ERROR
    # Apply saved choices only when the program actually starts. Importing this
    # module (for tests, packaging or tooling) must not mutate process state.
    try:
        apply_saved_environment()
    except ValueError as exc:
        # A corrupt settings file must be visible, but it must not make the
        # setup doctor unavailable. The setup report contains the same error.
        _SETUP_SETTINGS_ERROR = str(exc)
    else:
        _SETUP_SETTINGS_ERROR = None
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
    parser.add_argument("--tier", choices=("lean", "core", "full"), help="Tool schema tier")
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
    parser.add_argument("--setup", action="store_true", help="Run safe setup/onboarding")
    parser.add_argument("--setup-doctor", action="store_true", help="Run setup preflight only")
    parser.add_argument("--setup-dry-run", action="store_true", help="Plan setup without changes")
    parser.add_argument("--setup-noninteractive", action="store_true", help="Use provided/default setup values without prompts")
    parser.add_argument("--setup-name", type=str, help="Assistant display name")
    parser.add_argument("--setup-user-name", type=str, help="User display name")
    parser.add_argument("--setup-workspace", type=str, help="Seven workspace path")
    parser.add_argument("--setup-text-model", type=str, help="Ollama text model")
    parser.add_argument("--setup-vision-model", type=str, help="Ollama vision model")
    parser.add_argument("--setup-voice", choices=("auto", "edge", "pyttsx3", "none"), help="Voice engine")
    parser.add_argument("--setup-camera", choices=("off", "webcam", "screen", "both"), help="Camera/screen mode")
    parser.add_argument("--setup-startup", choices=("unchanged", "talk", "quiet", "none"), help="Login startup mode")
    parser.add_argument("--setup-install-ollama", action="store_true", help="Explicitly run the official Windows winget Ollama install command")
    parser.add_argument("--setup-pull-models", action="store_true", help="Explicitly pull selected Ollama models")
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

    if _SETUP_SETTINGS_ERROR and not (args.setup or args.setup_doctor):
        print(
            f"Seven cannot safely load its saved setup: {_SETUP_SETTINGS_ERROR}\n"
            "Run `python -m seven --setup-doctor` to inspect it or "
            "`python -m seven --setup` to replace it.",
            file=sys.stderr,
        )
        return 2

    if args.setup or args.setup_doctor:
        import json
        from seven.setup_wizard import (
            SetupOptions,
            doctor,
            interactive_options,
            run_setup,
        )
        data_dir = Path(os.getenv("SEVEN_DATA_DIR", Path.home() / ".seven"))
        workspace = Path(os.getenv("SEVEN_WORKSPACE", data_dir / "workspace"))
        ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        if args.setup_doctor and not args.setup:
            result = doctor(
                data_dir=data_dir,
                workspace=workspace,
                ollama_url=ollama_url,
            )
            if _SETUP_SETTINGS_ERROR:
                result["ok"] = False
                result["ready"] = False
                result["errors"].append(_SETUP_SETTINGS_ERROR)
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("ok") else 1
        options = SetupOptions(
            assistant_name=args.setup_name or os.getenv("SEVEN_NAME", "Seven"),
            user_name=args.setup_user_name or os.getenv("SEVEN_USER_NAME", os.getenv("USERNAME", "User")),
            workspace=Path(args.setup_workspace or workspace),
            text_model=args.setup_text_model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            vision_model=args.setup_vision_model or os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision"),
            voice_engine=args.setup_voice or os.getenv("SEVEN_TTS", "edge"),
            camera_mode=args.setup_camera or ("webcam" if os.getenv("SEVEN_CAMERA", "0") == "1" else "off"),
            startup_mode=args.setup_startup or "unchanged",
            data_dir=data_dir,
            ollama_url=ollama_url,
            install_ollama=args.setup_install_ollama,
            pull_models=args.setup_pull_models,
            dry_run=args.setup_dry_run,
            noninteractive=args.setup_noninteractive,
        )
        if not options.noninteractive:
            options = interactive_options(options)
        result = run_setup(options)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("ok") else 1

    from seven import config

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
