"""One-shot owner migration for cancelling a stuck Seven plan."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from seven.memory.store import Memory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--plan-id", type=int, required=True)
    parser.add_argument(
        "--reason",
        default="owner-authorized stuck-plan cancellation",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Without this flag the command is read-only.",
    )
    args = parser.parse_args()

    if args.apply:
        memory = Memory(args.db)
        before = memory.get_plan(args.plan_id)
    else:
        uri = f"file:{args.db.resolve().as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM plans WHERE id=?", (args.plan_id,)
            ).fetchone()
        before = dict(row) if row else None
    if not before:
        print(json.dumps({"ok": False, "reason": "plan_not_found"}))
        return 2
    if not args.apply:
        print(
            json.dumps(
                {
                    "ok": True,
                    "applied": False,
                    "plan_id": args.plan_id,
                    "status": before.get("status"),
                    "linked_goal_id": before.get("goal_id"),
                }
            )
        )
        return 0

    after = memory.cancel_plan(
        args.plan_id,
        reason=args.reason,
        block_linked_goal=True,
    )
    goal = (
        memory.get_goal(int(after["goal_id"]))
        if after and after.get("goal_id") is not None
        else None
    )
    print(
        json.dumps(
            {
                "ok": True,
                "applied": True,
                "plan_id": args.plan_id,
                "plan_status": (after or {}).get("status"),
                "linked_goal_id": (after or {}).get("goal_id"),
                "linked_goal_status": (goal or {}).get("status"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
