# Seven 4.5.0 exact change manifest — 2026-07-30

## Git boundary

- before commit:
  `2a1e36adc883e0fea689470f8b027e30365f349f`;
- implementation commit:
  `4791bac706336da9227808fc729c7e1b8018cf89`;
- deployment-evidence commit:
  `0e7312a3729e0682a7e2d9b8ce6cd83e46c93ea2`;
- pushed branch: `origin/codex/seven-completion`;
- remote head was verified at the deployment-evidence commit.

The implementation commit changed 36 files: 2,125 inserted lines and 122
deleted lines, plus two binary avatar sheets.

## Exact implementation changed-file list

Modified:

- `HANDOFF.md`
- `README.md`
- `ROADMAP.md`
- `deploy/peanut/config/seven-core.env.example`
- `deploy/peanut/static/index.html`
- `docs/INSTALLATION.md`
- `pyproject.toml`
- `seven/__init__.py`
- `seven/__main__.py`
- `seven/agent/loop.py`
- `seven/agent/prompt.py`
- `seven/config.py`
- `seven/identity/IDENTITY.md`
- `seven/identity/SOUL.md`
- `seven/identity/USER.md`
- `seven/memory/store.py`
- `seven/mind/episodic.py`
- `seven/mind/freewill.py`
- `seven/mind/state.py`
- `seven/runtime/startup.py`
- `seven/tools/mind_tools.py`
- `seven/tools/registry.py`
- `seven/ui/api_server.py`
- `tests/test_memory_ops.py`
- `uv.lock`

Added:

- `docs/SEVEN_4_5_0_IMPLEMENTATION_2026-07-30.md`
- `docs/SEVEN_LEGACY_RECOVERY_LEDGER_2026-07-30.md`
- `docs/SEVEN_RECOVERY_BEFORE_STATE_2026-07-30.md`
- `seven/assets/avatar/seven-pose-sheet-magenta.png`
- `seven/assets/avatar/seven-pose-sheet.png`
- `seven/mind/affect.py`
- `seven/mind/reflection.py`
- `seven/mind/relationship.py`
- `seven/ui/avatar.py`
- `tests/test_avatar.py`
- `tests/test_persistent_mind.py`

The deployment-evidence commit subsequently changed only:

- `HANDOFF.md`
- `deploy/peanut/config/seven-core.env.example`
- `docs/SEVEN_4_5_0_IMPLEMENTATION_2026-07-30.md`

## Preserved pre-existing drift

The following user changes were present before the implementation and remain
uncommitted and byte-identical:

- `deploy/peanut/README.md`:
  `1F627C5CAEA675469BBA31BBC7549C583415FC3BF3E5EE1B8C4CE5CF233A4929`;
- `docs/COMPLETION_LEDGER.md`:
  `85D87D51456FF1DE921C7EEB8457DB68AA979C546B926CFDF8F4FF0A25137643`.

They were not staged, reverted, reformatted or overwritten.

## Build and deployment artifacts

- wheel:
  `dist/seven_ai-4.5.0-py3-none-any.whl`;
- wheel SHA-256:
  `CAE3EDA173AB1ACA34B030CE6A375F09A075A197A7DEF8DEACEFA985FED5DEBA`;
- exact implementation-source archive:
  `outputs/seven-4.5.0-4791bac.tar.gz`;
- source SHA-256:
  `B6AC73982A3422B0E4E6F96AF6CC745CAE5C5CFE1B75B624EAE905B43B74E1A8`;
- transparent runtime pose sheet SHA-256:
  `8FA5414142C42DA6D2ABE72CBC205D3511960059F42DEE4D85F29B15B741B037`;
- preserved chroma-key source sheet SHA-256:
  `660FD3A6D43FB6B5499C44EEF74C95D6C22C0CCC1B6F60942A473C405A0926D8`.

## Validation summary

- full automated suite: `214 passed`;
- focused mind/avatar/API/loop suite: `62 passed`;
- wheel verification: passed;
- isolated 4.4.4 -> 4.5.0 install/upgrade/uninstall lifecycle: passed;
- Windows health/mind/direct reply/avatar: passed;
- Peanut core/web/public health, direct reply, project catalog, schema
  integrity and backup: passed;
- Ollama loaded-model metadata was unchanged across non-model smoke tests;
- no general model-backed chat, vision, speech-quality or soak claim was made.

Detailed runtime and backup proof is in
`SEVEN_4_5_0_IMPLEMENTATION_2026-07-30.md`.
