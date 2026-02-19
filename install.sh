#!/bin/bash
# ============================================
# Seven AI Assistant - macOS/Linux Installer
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  SEVEN AI ASSISTANT - Installation"
echo "================================================"
echo ""
echo "  Version: 2.6.0 (Advanced Sentience Architecture)"
echo ""
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/SevenAI"
OS="$(uname -s)"

# ---- Step 1: Check Python ----
echo -e "${CYAN}[Step 1/7] Checking Python installation...${NC}"

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}[ERROR] Python is not installed!${NC}"
    echo ""
    echo "Please install Python 3.11 or higher:"
    if [ "$OS" = "Darwin" ]; then
        echo "  brew install python@3.11"
        echo "  or download from: https://www.python.org/downloads/"
    else
        echo "  sudo apt install python3 python3-pip    (Debian/Ubuntu)"
        echo "  sudo dnf install python3 python3-pip    (Fedora)"
        echo "  sudo pacman -S python python-pip         (Arch)"
    fi
    echo ""
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}[OK] $PYTHON_VERSION${NC}"

# ---- Step 2: Check Python version ----
echo -e "${CYAN}[Step 2/7] Verifying Python version...${NC}"

$PYTHON_CMD -c "
import sys
if sys.version_info < (3, 11):
    print(f'Python {sys.version_info.major}.{sys.version_info.minor} is too old. 3.11+ required.')
    sys.exit(1)
" || {
    echo -e "${RED}[ERROR] Python 3.11 or higher is required!${NC}"
    exit 1
}

echo -e "${GREEN}[OK] Python version is compatible!${NC}"
echo ""

# ---- Step 3: Setup install directory ----
echo -e "${CYAN}[Step 3/7] Setting up installation directory...${NC}"

mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}[OK] Installation directory: $INSTALL_DIR${NC}"
echo ""

# ---- Step 4: Copy files ----
echo -e "${CYAN}[Step 4/7] Copying application files...${NC}"

cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR"/.* "$INSTALL_DIR/" 2>/dev/null || true
echo -e "${GREEN}[OK] Files copied!${NC}"
echo ""

# ---- Step 5: Install dependencies ----
echo -e "${CYAN}[Step 5/7] Installing Python dependencies...${NC}"
echo "This may take a few minutes..."
echo ""

cd "$INSTALL_DIR"
$PYTHON_CMD -m pip install --upgrade pip 2>/dev/null || true
$PYTHON_CMD -m pip install -r requirements.txt || {
    echo ""
    echo -e "${YELLOW}[WARNING] Some dependencies failed to install.${NC}"
    echo "Seven will still work, but some features may be limited."
    echo "You can install missing dependencies later with:"
    echo "  pip install -r requirements.txt"
    echo ""
}

echo -e "${GREEN}[OK] Dependencies installed!${NC}"
echo ""

# ---- Step 6: Install Ollama ----
echo -e "${CYAN}[Step 6/7] Checking Ollama installation...${NC}"

if command -v ollama &>/dev/null; then
    OLLAMA_VER=$(ollama --version 2>&1)
    echo -e "${GREEN}[OK] Ollama is already installed: $OLLAMA_VER${NC}"
else
    echo "Ollama is not installed."
    echo ""
    read -p "Install Ollama automatically? (Y/n): " INSTALL_OLLAMA
    INSTALL_OLLAMA=${INSTALL_OLLAMA:-Y}

    if [[ "$INSTALL_OLLAMA" =~ ^[Yy] ]]; then
        echo ""
        if [ "$OS" = "Darwin" ]; then
            echo "Downloading Ollama for macOS..."
            TMPFILE=$(mktemp /tmp/Ollama-darwin.XXXXXX.zip)
            curl -fSL "https://ollama.com/download/Ollama-darwin.zip" -o "$TMPFILE"
            echo "Extracting to /Applications..."
            unzip -o "$TMPFILE" -d /Applications
            rm -f "$TMPFILE"
            echo -e "${GREEN}[OK] Ollama installed to /Applications${NC}"
            echo ""
            echo "Please open Ollama.app from /Applications to start the service."
            echo "Then press Enter to continue..."
            read -r
        else
            echo "Installing Ollama via official script..."
            curl -fsSL https://ollama.com/install.sh | sh
            echo -e "${GREEN}[OK] Ollama installed!${NC}"
        fi
    else
        echo ""
        echo "Please install Ollama manually:"
        if [ "$OS" = "Darwin" ]; then
            echo "  Download from: https://ollama.com/download"
        else
            echo "  curl -fsSL https://ollama.com/install.sh | sh"
        fi
        echo ""
    fi
fi

echo ""

# ---- Check Ollama server and pull model ----
echo "Checking for llama3.2 model..."

# Wait briefly for server
OLLAMA_READY=false
for i in $(seq 1 10); do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        OLLAMA_READY=true
        break
    fi
    sleep 1
done

if [ "$OLLAMA_READY" = false ]; then
    echo -e "${YELLOW}[WARNING] Ollama server is not responding.${NC}"
    echo ""

    if [ "$OS" = "Linux" ] && command -v ollama &>/dev/null; then
        echo "Attempting to start Ollama service..."
        ollama serve &>/dev/null &
        sleep 5
        if curl -s http://localhost:11434/api/tags &>/dev/null; then
            OLLAMA_READY=true
            echo -e "${GREEN}[OK] Ollama server started!${NC}"
        fi
    fi

    if [ "$OLLAMA_READY" = false ]; then
        echo "Please start Ollama and then run:"
        echo "  ollama pull llama3.2"
        echo ""
    fi
fi

if [ "$OLLAMA_READY" = true ]; then
    if ollama list 2>/dev/null | grep -qi "llama3.2"; then
        echo -e "${GREEN}[OK] llama3.2 model found!${NC}"
    else
        echo "llama3.2 model not found."
        read -p "Download llama3.2 now? (~2GB) (Y/n): " PULL_MODEL
        PULL_MODEL=${PULL_MODEL:-Y}

        if [[ "$PULL_MODEL" =~ ^[Yy] ]]; then
            echo ""
            ollama pull llama3.2 || {
                echo ""
                echo -e "${YELLOW}[WARNING] Model download failed. Retry later with:${NC}"
                echo "  ollama pull llama3.2"
            }
        else
            echo ""
            echo "You'll need to run 'ollama pull llama3.2' before using Seven."
        fi
    fi

    # Check for vision model
    if ollama list 2>/dev/null | grep -qi "llama3.2-vision"; then
        echo -e "${GREEN}[OK] llama3.2-vision model found!${NC}"
    else
        echo "llama3.2-vision model not found (needed for screen/webcam vision)."
        read -p "Download llama3.2-vision now? (~8GB) (Y/n): " PULL_VISION
        PULL_VISION=${PULL_VISION:-Y}

        if [[ "$PULL_VISION" =~ ^[Yy] ]]; then
            echo ""
            ollama pull llama3.2-vision || {
                echo ""
                echo -e "${YELLOW}[WARNING] Vision model download failed. Retry later with:${NC}"
                echo "  ollama pull llama3.2-vision"
            }
        else
            echo ""
            echo "Vision features will be limited without llama3.2-vision."
        fi
    fi
fi

echo ""

# ---- Step 7: Run setup wizard ----
echo -e "${CYAN}[Step 7/7] Launching setup wizard...${NC}"
echo ""

$PYTHON_CMD setup_wizard.py || {
    echo ""
    echo -e "${YELLOW}[WARNING] Setup wizard failed or was skipped.${NC}"
    echo "You can run it later with: python3 setup_wizard.py"
    echo ""
}

# ---- Create launcher script ----
LAUNCHER="$INSTALL_DIR/seven"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 main.py "$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

# Symlink to ~/.local/bin if it exists
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$LAUNCHER" "$HOME/.local/bin/seven"
    echo -e "${GREEN}[OK] 'seven' command installed to ~/.local/bin/seven${NC}"
fi

# ---- Done ----
echo ""
echo "================================================"
echo -e "  ${GREEN}${BOLD}INSTALLATION COMPLETE!${NC}"
echo "================================================"
echo ""
echo "Seven AI Assistant has been installed to:"
echo "  $INSTALL_DIR"
echo ""
echo "To launch Seven:"
echo "  1. Run: seven"
if [ -d "$HOME/.local/bin" ]; then
echo "     (or: ~/.local/bin/seven)"
fi
echo "  2. Or: cd $INSTALL_DIR && python3 main.py"
echo ""
echo "Documentation:"
echo "  - Quick Start: README.md"
echo "  - Setup Guide: SETUP.md"
echo ""
echo "================================================"
echo ""

read -p "Launch Seven now? (Y/n): " LAUNCH
LAUNCH=${LAUNCH:-Y}

if [[ "$LAUNCH" =~ ^[Yy] ]]; then
    echo ""
    echo "Launching Seven..."
    cd "$INSTALL_DIR"
    $PYTHON_CMD main.py
fi

echo ""
echo "Thank you for installing Seven!"
echo ""
