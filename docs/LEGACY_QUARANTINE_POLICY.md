# Legacy quarantine policy

`_legacy/v3/` is a frozen, import-inert archaeological snapshot. It is not packaged by `pyproject.toml`, is never added to `sys.path`, and must not be imported by supported `seven/` code. Git history plus the per-file hashes in `FILE_INVENTORY.csv` preserve evidence without presenting the old tree as a second product.

Every tracked path receives one deterministic final disposition from `scripts/generate_file_inventory.py`:

- `quarantined-recovered`: useful behavior has a tested, documented replacement under `seven/`.
- `quarantined-excluded`: reviewed capability is outside the Seven 4.4 contract or cannot be truthfully supported without an external provider/device contract.
- `quarantined-rejected`: random, template-driven, or theatrical cognition/sentience behavior is intentionally not a product capability.
- `quarantined-migration-evidence`: old data/fixtures exist only to prove migration behavior and are never automatically loaded.
- `quarantined-test-reference`: historical tests are reference material, not current release evidence.
- `quarantined-history`: old audits and claims are explicitly non-authoritative.
- `quarantined-superseded`: obsolete installers/launchers are replaced by the supported packaging and CLI lifecycle.
- `quarantined-reference`: inspected residue with no unique supported behavior; retained only for archaeology.

The classifications are filename/capability policy, not a security scanner. `LEGACY_SYMBOL_INVENTORY.csv` separately records every legacy Python file, its hash, parse status, imports, classes, and functions. `LEGACY_RECOVERY_MATRIX.md` records product-level recovery decisions and `COMPLETION_LEDGER.md` records the implementation evidence.

## Release rule

No unresolved `review-*` disposition may exist in the generated inventory. No supported runtime module may import `_legacy`, `integrations`, `extensions`, or other v3 top-level packages. The wheel verifier proves only `seven` packages ship.

The quarantine remains in the source repository for lossless archaeology but is excluded from wheels and installed systems. A future deletion requires a separately reviewed archival release/tag; cleanup alone is not permission to discard evidence.
