# Development and Release Process

## Source of truth

`seven/` is the only supported runtime. `_legacy/v3/` is a fully classified, import-inert recovery archive governed by `LEGACY_QUARANTINE_POLICY.md`. New behavior follows the focused boundaries in `AGENTS.md`.

## Record required for material changes

Document the problem and impact, files inspected, selected behavior, rejected alternatives, configuration/data migration, automated validation, hardware/manual validation, documentation, and remaining limitations.

## Removal policy

No file is removed merely because it is old or untidy. Classify it first:

- **Keep:** authoritative history, fixture, migration input or supported compatibility surface.
- **Port:** behavior worth reimplementing in the modern package.
- **Archive:** historically useful but inappropriate for the main runtime tree.
- **Remove:** generated output, superseded duplicate, false audit artifact, sensitive data or content without engineering value.

Record the reason and replacement/migration path in the inventory.

## Verification levels

- **Unit:** deterministic behavior without live Ollama/hardware.
- **Integration:** multiple Seven modules with controlled dependencies.
- **Live model:** supported Ollama models and real tool calls.
- **System:** installed package, service, GUI and filesystem lifecycle.
- **Hardware:** audio, camera, displays, GPU and robotics devices.
- **Soak:** long-running autonomy, resource stability and recovery.
- **Release:** clean install, upgrade, uninstall, migration and documentation dry run.

No feature is complete until the required levels pass and evidence is recorded in `COMPLETION_LEDGER.md`.

## Dependency changes

Edit only `pyproject.toml`, then run `uv lock` and `uv lock --check`. Commit both files together. `requirements-real.txt` is a compatibility redirect and must not regain duplicated package/version lines. Build the wheel and run `verify_install_lifecycle.py`; for schema or packaging changes, include `--previous-wheel` and record both versions and schema evidence in the completion ledger.

## Inventory before commit

Run both inventory generators before staging. The tracked-file generator includes cached files and non-ignored untracked files, so newly created source, tests and documentation appear in the same commit's evidence. Generated inventory CSVs exclude themselves.
