"""python -m seven"""
from __future__ import annotations

import argparse
import logging
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
            logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
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
    parser.add_argument(
        "--no-freewill",
        action="store_true",
        help="Disable free will (not recommended)",
    )
    args = parser.parse_args(argv)

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
        run_api_blocking()
        return 0

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
