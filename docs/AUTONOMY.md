# Seven Real — Autonomy

No greeting loops. Work only when there is something real to do.

## Concepts

| Concept | Meaning |
|---|---|
| **Goal** | Long-running objective (`add_goal` tool or ask Seven) |
| **Task** | Todo, optionally with `due_at` |
| **Heartbeat** | Background tick (default 5 min) — acts only if overdue tasks / goals / work session |
| **Work session** | Focus one goal for N minutes (`/work`) |
| **Goal step** | One tool-using turn; progress rises **only if real tools ran** |

## Commands

```
/goals
/work <goal_id> [minutes]   # default minutes from SEVEN_WORK_MINUTES (15)
/workstep [goal_id]         # one step now
/workstatus
/stopwork
/audit [n]                  # pretty activity log
```

## Progress rules

1. Agent is prompted to use tools (`run_shell`, `write_file`, `run_python`, …).
2. After the turn, Seven checks the **audit log delta**.
3. Only “real work” tools count (not `list_goals`, `search_memory`, `get_system_info`, …).
4. If real tools ran → progress += small amount (capped), note written under title `autonomy`.
5. If no real tools → **progress unchanged**.

## Env

| Var | Default | Meaning |
|---|---|---|
| `SEVEN_HEARTBEAT` | `300` | Seconds between ticks |
| `SEVEN_AUTONOMY_IDLE` | `10` | Minutes idle before chasing goals |
| `SEVEN_AUTONOMY_MIN_INTERVAL` | `60` | Min seconds between auto steps |
| `SEVEN_WORK_MINUTES` | `15` | Default work session length |

## Example

```text
User> Create a goal to write a README in my workspace summarizing Seven Real.
Seven> (uses add_goal + maybe write_file)

User> /goals
#1 Write README — 0%

User> /work 1 20
Work session ON …

User> /workstep 1
goal=#1 … real_work=1 tools=[write_file] progress 0%→5%
```

Heartbeat will continue that goal until the session ends or progress hits 100%.
