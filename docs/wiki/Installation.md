# Installation

Seven AI runs on Windows, macOS, and Linux. The recommended setup is Python 3.11+ with a local Ollama install.

---

## System Requirements

**Minimum**:
- Windows 10/11 (64-bit), macOS 10.15+, or modern Linux
- Python 3.11+
- 8 GB RAM
- 500 MB storage + ~4 GB for Ollama models
- Microphone + speakers (for voice mode)

**Recommended**:
- 16 GB RAM
- NVIDIA GPU with 6 GB+ VRAM (Ollama + Whisper both benefit)

**Optimal (everything on, vision + Whisper)**:
- 32 GB RAM
- 8 GB+ VRAM GPU

---

## 1. Install Prerequisites

### Python 3.11+
https://www.python.org/downloads/ — **check "Add Python to PATH" during install**.

### Ollama
https://ollama.com/download

After install:
```bash
ollama pull llama3.2
ollama pull llama3.2-vision  # optional, for vision features
```

### opencode (optional, for the delegator extension)
```bash
npm install -g opencode-ai
opencode auth login  # configure a provider once
```

---

## 2. Get Seven

**Option A — git clone (recommended)**:
```bash
git clone https://github.com/LoSkroefie/seven-ai.git
cd seven-ai
```

**Option B — download release**:
Download the [latest release zip](https://github.com/LoSkroefie/seven-ai/releases/latest) and extract.

---

## 3. Install Dependencies

### Windows
```
install.bat
```

### Linux/macOS
```bash
chmod +x install.sh
./install.sh
```

The installer:
- Verifies Python and Ollama
- Installs `requirements.txt`
- Runs `setup_wizard.py`
- Creates desktop shortcuts

---

## 4. First Launch

### Windows (v3.2.20+, recommended)
```
run_seven.bat
```

This pins the Python interpreter so Whisper / MCP / torch all resolve. Critical on systems where Windows Store Python shadows your real env.

### Any OS
```bash
python main_with_gui_and_tray.py
```

---

## Data Location

Seven stores everything under `~/.chatbot/`:
- `memory.db` — SQLite conversation database
- `bot.log` — runtime log
- `bot_name.txt` — her current name
- `instance_name.txt` — this install's instance name

Your data persists across updates. Safe to delete this folder for a clean slate.

---

## Upgrading

```bash
git pull origin main
# re-run install.bat or install.sh if dependencies changed
```

Your memories, settings, and identity are preserved across upgrades.

---

## Next

- [First Launch](First-Launch)
- [Configuration Reference](Configuration-Reference)
- [Troubleshooting](Troubleshooting)
