# opencode Delegator

New in **v3.2.20**: Seven can hand coding and analysis tasks off to the [opencode](https://github.com/sst/opencode) CLI via natural-language triggers.

---

## Setup

### 1. Install opencode
```bash
npm install -g opencode-ai
```

### 2. Configure a provider
```bash
opencode auth login
```

Pick any provider opencode supports (Anthropic, OpenAI, Ollama, etc.). Seven doesn't care which — she just invokes the CLI.

### 3. Enable in Seven's config
```python
# config.py (auto-enabled if opencode is on PATH)
ENABLE_OPENCODE_DELEGATOR = True
OPENCODE_ALLOW_BUILD = False       # destructive mode, opt-in
OPENCODE_DEFAULT_AGENT = "plan"    # read-only by default
OPENCODE_TIMEOUT_SECONDS = 180
OPENCODE_WORKING_DIR = None        # None = current directory
OPENCODE_MAX_REPLY_CHARS = 4000    # truncate long output
```

---

## Triggers

Seven recognizes these patterns (case-insensitive):

| Pattern | Example |
|---------|---------|
| `opencode, <task>` | `opencode, explain the main loop` |
| `opencode: <task>` | `opencode: review the auth flow` |
| `ask opencode to <task>` | `ask opencode to summarize this file` |
| `delegate to opencode: <task>` | `delegate to opencode: list the TODOs` |
| `hey opencode <task>` | `hey opencode, what does this function do?` |
| `opencode status` | Returns version + stats |
| `opencode version` | Returns CLI version |
| `is opencode ready?` | Status check |

---

## Agents

### Plan Agent (default — safe)
Read-only. Analyzes code, proposes changes, doesn't touch files.

```
You: opencode, what's in core/whisper_voice.py?
Seven: [opencode/plan, 4.2s]
This module implements WhisperVoiceManager — a speech-recognition wrapper around OpenAI Whisper...
```

### Build Agent (opt-in — destructive)
CAN modify files. Off by default.

To enable:
```python
OPENCODE_ALLOW_BUILD = True
```

Then prefix tasks with `build:`:
```
You: opencode build: add a docstring to every function in voice.py
Seven: [opencode/build, 12.4s]
Modified core/voice.py. Added 7 docstrings...
```

Even with `OPENCODE_ALLOW_BUILD = True`, the `build:` prefix is required — casual mentions of "fix" or "modify" don't trigger destructive mode.

---

## Output Format

Seven prefixes opencode responses with a header:
```
[opencode/plan, 3.1s]
<opencode's answer>
```

Or the time field tracks the actual CLI invocation time.

Long responses are truncated at `OPENCODE_MAX_REPLY_CHARS` (default 4000). Raise if you delegate large analysis tasks.

---

## Working Directory

By default, opencode runs in Seven's working directory. Set `OPENCODE_WORKING_DIR` to pin it to a specific repo:

```python
OPENCODE_WORKING_DIR = "C:/Users/You/projects/myrepo"
```

Seven will always point opencode at that repo regardless of where she was launched from.

---

## Troubleshooting

### "opencode CLI isn't available"
```bash
npm install -g opencode-ai
where opencode  # Windows
which opencode  # Linux/macOS
```

Make sure the binary is on PATH. If `where opencode` returns a path but Seven still says unavailable, restart Seven so it re-scans PATH.

### opencode hangs on first run
```bash
opencode auth login
```

You need to configure a provider once. Seven's wrapper has a 180s timeout and will return a clean error if opencode never responds.

### Timeouts on big tasks
Raise `OPENCODE_TIMEOUT_SECONDS`. Default 180s is fine for small queries but multi-file analysis may need 600s+.

---

## Under the Hood

Seven wraps opencode via `subprocess.run`:

```python
# integrations/opencode.py
result = subprocess.run(
    ["opencode", "run", "--agent", "plan", "<task>"],
    capture_output=True, text=True, timeout=180,
)
```

No API calls from Seven. opencode does whatever it's configured to do (local Ollama, cloud provider, whatever).

Source: [`integrations/opencode.py`](https://github.com/LoSkroefie/seven-ai/blob/main/integrations/opencode.py) · [`extensions/opencode_delegator.py`](https://github.com/LoSkroefie/seven-ai/blob/main/extensions/opencode_delegator.py)
