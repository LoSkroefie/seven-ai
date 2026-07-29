# Safe setup and onboarding

Seven's supported setup engine is:

```text
python -m seven --setup
```

It replaces the archived v3 source-copy wizard. It does not edit source files,
accept API keys, delete existing data, delete Ollama models, or execute a
downloaded remote shell script.

## Preflight and dry run

```text
python -m seven --setup-doctor
python -m seven --setup --setup-dry-run --setup-noninteractive
```

Doctor reports the Python executable/version, platform, data/workspace paths,
free disk, system RAM, Ollama executable/API/version/models, and current package
installation commands. Missing Ollama is visible as a readiness warning.

Dry-run validates every value and prints the complete plan without creating a
workspace, settings file, startup entry, virtual environment, or model.

## Saved choices

Setup records only non-secret choices in
`SEVEN_DATA_DIR/settings.json` (normally `~/.seven/settings.json`):

- assistant and user display names;
- workspace path;
- text and vision model names;
- voice engine;
- camera/screen mode;
- login-startup mode.

Writes use a same-directory temporary file, flush, `fsync`, atomic replacement,
and owner-only mode where the platform supports it. Unknown fields are retained
for forward compatibility. Explicit environment variables always override saved
defaults.

API keys remain environment/provider configuration. Setup has no API-key
argument and never writes credentials into source or settings.

## Noninteractive example

```text
python -m seven --setup --setup-noninteractive ^
  --setup-name Seven ^
  --setup-user-name User ^
  --setup-workspace C:\SevenWorkspace ^
  --setup-text-model qwen2.5:7b ^
  --setup-vision-model llama3.2-vision ^
  --setup-voice edge ^
  --setup-camera off ^
  --setup-startup talk
```

Valid startup choices are `unchanged`, `talk`, `quiet`, and `none`. `none`
removes only Seven's owned login-startup entry; it does not uninstall Seven or
remove data.

## Ollama and models

Setup discovers the configured Ollama endpoint and lists installed models.
Model names are validated and passed as individual process arguments.

No Ollama installation or model download happens by default. Explicit flags:

```text
python -m seven --setup --setup-install-ollama
python -m seven --setup --setup-pull-models
```

On Windows, the installation flag runs the official Winget package command for
`Ollama.Ollama`. If Winget is unavailable, setup fails visibly and reports
<https://ollama.com/download>. Automatic Ollama installation is disabled on
Linux/macOS so Seven never executes `curl | sh`; follow the official instructions
manually.

Text and vision models can require several GiB each. Doctor warns below 10 GiB
free disk or 8 GiB RAM. Pull failures are returned with command, return code and
bounded output. Setup never deletes or replaces another installed model.

## Failure and recovery contract

- Invalid values fail before any write.
- Dry-run performs no setup mutation.
- External install/download failures stop before settings/startup changes.
- Existing settings are merged, not discarded.
- `SEVEN_DATA_DIR`, memories and backups are never removed.
- The installer wrappers do not implement uninstall.

For backup and restore, use [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).
For package removal, follow [INSTALLATION.md](INSTALLATION.md); user data remains
preserved unless the user separately and explicitly removes it.
