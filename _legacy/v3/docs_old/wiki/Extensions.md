# Extensions

Seven ships with **20 loaded extensions** in v3.2.20. They're auto-discovered from the `extensions/` directory, hot-reloadable via the REST API, and can hook into:
- `on_message(user_input, bot_response)` — return a string to augment Seven's reply
- `run(context)` — scheduled execution on interval
- `init(bot)` — one-shot setup on plugin load

---

## Loaded Extensions (20)

### Passive / Message-Driven

| Name | Trigger | Purpose |
|------|---------|---------|
| **opencode_delegator** | "opencode, X" | Hand tasks to opencode CLI (v3.2.20) |
| **conversation_memory** | All messages | Store conversations with mood/topic/sentiment |

### Scheduled

14 extensions run on intervals via the plugin scheduler (fixed in v3.2.20 — BUG-R4):

| Name | Interval | Purpose |
|------|----------|---------|
| `smart_reminders` | 1m | Fire reminders when due |
| `ambient_listener` | 15m | Passive Whisper capture (off by default) |
| `motivation_engine` | 30m | Proactive motivational nudges |
| `system_health` | 30m | CPU/RAM/disk check (was 5m, throttled in v3.2.20) |
| `uptime_monitor` | 60m | Bot uptime stats (was 10m) |
| `action_item_digest` | 60m | Scan conversations for action items |
| `mood_tracker` | 60m | Log Seven's mood trajectory |
| `habit_tracker` | 120m | Recognize user daily patterns |
| `weather_reporter` | 180m | Weather updates |
| `news_digest` | 240m | Summarize news |
| `learning_journal` | 480m | Seven's learning notes |
| `daily_digest` | 720m | Daily recap |
| `auto_backup` | 1440m | Daily DB backup |
| `quote_of_the_day` | 1440m | Morning quote |

### Non-scheduled, feature-specific
The other 4 extensions handle hooks like command parsing, UI integration, or specific event triggers.

---

## Enabling / Disabling

Most extensions have a config flag in `config.py`:
```python
ENABLE_AMBIENT_LISTENER = False
ENABLE_ACTION_ITEM_DIGEST = False
ENABLE_OPENCODE_DELEGATOR = True
# ... etc
```

Check the top of each extension file for its flag name.

---

## REST API

```bash
GET  http://127.0.0.1:7777/extensions          # list loaded plugins
POST http://127.0.0.1:7777/extensions/reload   # hot-reload all
GET  http://127.0.0.1:7777/v32/status          # combined v3.2 system status
```

---

## Writing Your Own

Minimal plugin skeleton — save as `extensions/my_plugin.py`:

```python
from utils.plugin_loader import SevenExtension

class MyExtension(SevenExtension):
    name = "My Plugin"
    version = "1.0"
    description = "Does something useful"
    author = "You"

    # Set to 0 for purely message-driven plugins
    schedule_interval_minutes = 60

    # Set True if you need access to Seven's Ollama client
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.enabled = True

    def on_message(self, user_message: str, bot_response: str):
        """Called on every user/bot message exchange.
        Return a string to append to Seven's reply, or None to stay silent."""
        if "hello my plugin" in user_message.lower():
            return "[my_plugin] Hi there!"
        return None

    def run(self, context: dict = None) -> dict:
        """Scheduled execution. Called every schedule_interval_minutes."""
        # Do your periodic work here
        return {"status": "ok", "message": "Ran!"}
```

Restart Seven or POST to `/extensions/reload`. Your plugin appears in `/extensions`.

---

## Pipeline (what actually runs when you send a message)

Fixed in v3.2.20 — all three of these paths now correctly dispatch to extensions:

1. **CLI / voice path**: `_main_loop` → `process_input()` → `_process_input()` → LLM reply → `plugin_loader.notify_message()` → return string(s) merged via `"\n\n".join()`
2. **Gradio web UI**: `gui/web_ui.py:50` calls `bot.process_input()` (was `_process_input` — BUG-R2)
3. **REST API `/chat`**: `seven_api.py` also routes through `process_input()` (BUG-R3 side-effect fix)

---

## Blocked Modules

The plugin loader sandboxes imports. These are blocked:
- `subprocess`, `shutil`, `ctypes`
- `multiprocessing`, `socket`
- `http.server`, `xmlrpc`
- `ftplib`, `smtplib`

Extensions that need these (like `opencode_delegator` for subprocess) have to request exceptions via config or be built into core rather than as sandboxed plugins. The opencode delegator works because subprocess is imported *inside* its method calls, not at module top-level.

---

## See Also

- [Writing Extensions](Writing-Extensions) — full authoring guide
- [REST API](REST-API) — hot-reload endpoints
- [opencode Delegator](opencode-Delegator) — example of a real extension
