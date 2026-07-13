# Versioned executable skills

Seven skills are reusable, ordered recipes of real registered tool calls. They are L4 workflows, not generated-code sandboxes. Each step has this shape:

```json
{"tool":"write_file","args":{"path":"notes.txt","content":"done"},"continue_on_error":false}
```

`save_skill` accepts a JSON array containing 1–50 steps. Names are bounded, descriptions are bounded, every step/tool/argument object is structurally validated, unknown or disabled tools are rejected, unsupported placeholder keys and credential-like argument keys are rejected, and a skill cannot recursively call `run_skill`. Saving changed content creates an immutable increasing revision; saving identical content is a visible no-op. Put credentials in the target tool's supported environment/configuration source rather than a durable recipe. Text embedded inside a shell command cannot be universally classified, so users must still avoid literal secrets there.

Tools:

- `save_skill` creates or revises a skill;
- `list_skills` shows current version plus successful/failed run counts;
- `skill_history` lists immutable revision metadata and provenance;
- `rollback_skill` validates an old revision and activates its content as a new revision, preserving history;
- `run_skill` preflights every step before executing the first one.

Execution stops on the first failed tool by default. `continue_on_error:true` permits later steps but the overall run remains failed. A result beginning with `ERROR` or structured JSON containing `"ok":false` counts as failure. Run history stores only version and per-tool booleans, not tool output, reducing duplicate retention of potentially sensitive data; the ordinary redacted audit log remains the detailed accountability source.

## Authority and rollback boundary

Validation proves a recipe is well formed and references currently active tools. It does not make those tools safe or reduce Seven's authority. Shell, file deletion, desktop input, SSH, coding-agent and robotics steps retain their real L4 effects.

Revision rollback changes which recipe will run next. It cannot undo filesystem changes, commands, messages, remote operations, robot movement, or any other effects produced by a prior run. Use the relevant backup/version-control/system recovery mechanism for those effects.

Extensions can disappear after a skill is saved. Run preflight detects unavailable tools before any step executes. Existing pre-v4 skill rows are preserved as revision 1 during schema migration; malformed historical recipes remain visible but cannot execute or be activated until replaced with a valid revision.

## Legacy disposition

The v3 self-scripting engine mixed LLM code generation, arbitrary files, an unsynchronized JSON registry, shared-process execution and a pattern scanner described as safety. Its timeout could leave descendants, its “safe” scan was bypassable, and overwrites had no rollback. Seven already has owned Python/shell execution and coding-agent tools for code; the durable reusable value is recovered here as validated, versioned tool workflows with process lifecycle inherited from the underlying tools.
