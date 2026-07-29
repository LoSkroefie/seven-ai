# Seven local Windows deployment — 2026-07-29

## Installed instance

- Install root: `D:\SevenLocal`
- Private data: `D:\SevenLocal\data`
- Workspace: `D:\SevenLocal\workspace`
- Isolated Python: `D:\SevenLocal\venv\Scripts\python.exe`
- Browser runtime: `D:\SevenLocal\ms-playwright`
- API: `http://127.0.0.1:18765` (loopback only, bearer-token protected)
- API launcher: `D:\SevenLocal\Start-Seven-API.cmd`
- Login startup: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Seven Talk.cmd`
- Text model: `qwen2.5:7b`
- Vision model: `moondream:latest`
- Neural voice: `en-US-AvaNeural`
- Tool tier: `full`
- Model-facing tool schema: `dispatcher`

The existing `C:\Users\USER-PC\.seven` installation was not modified. This is
an isolated local copy with its own database, browser profile, workspace,
launchers and logs.

## Grounded project roots

Seven can discover real projects beneath:

- `C:\Users\USER-PC\Documents\Codex`
- `C:\Users\USER-PC\Documents\New project`
- `C:\Users\USER-PC\dayzserver`
- `C:\Game Servers`
- `D:\Bordereau - claude`

Project answers come from the stored project catalog and real paths rather than
invented names.

## Implemented local capabilities

- Authenticated text chat and grounded project listing.
- Female neural speech plus offline speech fallback.
- Push-to-talk speech recognition with lazy local Whisper loading.
- Screen and webcam vision, with bounded JPEG normalization before inference.
- Persistent isolated Chromium browsing, extraction, click and form-fill tools.
- Structured document reading and PDF creation.
- Portable local calendar add/list/remove operations.
- Credential-safe SMTP send and IMAP listing tools; no credentials are stored
  in source or the install manifest.
- Full registered tool set, durable schema-6 memory, backups, audit records,
  goals, tasks, skills, reminders and model lifecycle controls.

## Runtime proof recorded

- API health returned `200`, service `seven-real`, version `4.4.4`.
- Authenticated chat greeted Jan as Seven in 26.55 seconds.
- Full-size Seven avatar JPEG was accepted by `/vision`, normalized internally,
  and described correctly in 34.63 seconds.
- `/speech` produced a 23,184-byte `audio/mpeg` response using Ava.
- Project catalog returned 16 real projects with paths.
- Browser extraction returned the `Example Domain` page.
- Calendar add/list/remove round trip completed and left no test event behind.
- A PDF was created and read back as one page.
- Memory schema 6 passed integrity and foreign-key checks.
- A portable backup was created beneath `D:\SevenLocal\data\backups`.

Proof artifacts are in `D:\SevenLocal\workspace\verification`. The local API
logs are `D:\SevenLocal\data\api.stdout.log` and
`D:\SevenLocal\data\api.stderr.log`.

## Honest limits

- Mail code is installed and tested without network credentials; actual send
  and mailbox access remain unconfigured.
- Whisper, audio devices and push-to-talk are installed, but no human
  microphone utterance was captured during unattended validation.
- Camera capability is installed but no camera frame was captured during the
  unattended run.
- `moondream:latest` works locally and fits available storage, but is a compact
  vision model. The locally advertised `llama3.2-vision` model was unusable
  because its large blob was missing; it was not presented as working.
- Ollama model swaps can make first responses take tens of seconds.
