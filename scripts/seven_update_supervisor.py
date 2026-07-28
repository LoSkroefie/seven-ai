"""Operator-only CLI for Seven's external update supervisor."""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict
from pathlib import Path

# Allow the checked-out source script to run before the package is installed.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from seven.runtime.update_supervisor import (
    CommandServiceController,
    ProcessRunner,
    UpdateSpec,
    UpdateSupervisor,
)


def _argv(value: str) -> tuple[str, ...]:
    parsed = tuple(shlex.split(value, posix=sys.platform != "win32"))
    if not parsed:
        raise argparse.ArgumentTypeError("command cannot be empty")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and atomically activate an isolated Seven release."
    )
    parser.add_argument("mode", choices=("plan", "dry-run", "apply"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--release-id")
    parser.add_argument(
        "--test-command",
        action="append",
        type=_argv,
        help="Repeatable argv command; defaults to the full pytest suite.",
    )
    parser.add_argument("--candidate-health-command", type=_argv)
    parser.add_argument("--restart-command", type=_argv)
    parser.add_argument("--service-health-command", type=_argv)
    parser.add_argument("--timeout", type=float, default=900)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = ProcessRunner()
    service = None
    if args.mode == "apply":
        if not args.restart_command or not args.service_health_command:
            raise SystemExit(
                "apply requires --restart-command and --service-health-command"
            )
        service = CommandServiceController(
            runner,
            args.restart_command,
            args.service_health_command,
            timeout=args.timeout,
        )
    spec_kwargs = {
        "source": args.source,
        "ref": args.ref,
        "release_id": args.release_id,
        "command_timeout": args.timeout,
    }
    if args.test_command:
        spec_kwargs["test_commands"] = tuple(args.test_command)
    if args.candidate_health_command:
        spec_kwargs["candidate_health_command"] = args.candidate_health_command
    spec = UpdateSpec(**spec_kwargs)
    report = UpdateSupervisor(args.root, runner=runner, service=service).run(
        spec, mode=args.mode
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
