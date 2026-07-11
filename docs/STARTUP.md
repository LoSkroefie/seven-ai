# Start Seven After Login

Seven's supported login entry launches companion talk mode, not the silent daemon. Talk mode initializes Ollama, voice, memory and free will, generates a short greeting and speaks it when TTS is available.

## Install

```text
python -m seven --install-startup
```

For machines that must never use the microphone or speakers at login:

```text
python -m seven --install-startup-quiet
```

Check or remove:

```text
python -m seven --startup-status
python -m seven --remove-startup
```

## Platform behavior

- Windows: installs a current-user command file in the Startup folder.
- Linux desktops: installs `~/.config/autostart/seven-companion.desktop`.
- macOS: installs `~/Library/LaunchAgents/ai.seven.companion.plist`.

The entry records the exact Python executable used to install it. Reinstall startup after moving/replacing that Python environment.

## Greeting behavior

`seven/ui/talk.py` refreshes living state and asks the configured model for one short natural opening sentence. When the model is unavailable, Seven uses an explicit degraded-mode greeting. A greeting is written to conversation memory with `talk_open=true`.

The legacy `install_autostart.ps1` starts daemon mode and remains a compatibility artifact during completion work. It does not satisfy spoken-login behavior and will be retired only after migration documentation and installed-system testing.
