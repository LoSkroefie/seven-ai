#!/bin/bash
# ============================================
# Seven AI Assistant - macOS/Linux Uninstaller
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/.local/share/SevenAI"
DATA_DIR="$HOME/.chatbot"

echo ""
echo "================================================"
echo "  SEVEN AI ASSISTANT - Uninstaller"
echo "================================================"
echo ""
echo "This will remove Seven AI Assistant from your computer."
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "The following will be removed:"
echo "  - Application files in $INSTALL_DIR"
echo "  - 'seven' command symlink (if exists)"
echo ""
echo -e "${YELLOW}NOTE: Your personal data in $DATA_DIR will be preserved.${NC}"
echo "You can manually delete it later if desired."
echo ""

read -p "Are you sure you want to uninstall? (y/N): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo ""
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Uninstalling..."
echo ""

# Remove symlink
if [ -L "$HOME/.local/bin/seven" ]; then
    echo "Removing 'seven' command..."
    rm -f "$HOME/.local/bin/seven"
    echo "  Done"
fi

# Remove install directory
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing application files..."
    rm -rf "$INSTALL_DIR"
    echo "  Done"
fi

echo ""
echo "================================================"
echo -e "  ${GREEN}${BOLD}UNINSTALL COMPLETE${NC}"
echo "================================================"
echo ""
echo "Seven AI Assistant has been removed."
echo ""
echo "Your personal data has been preserved in:"
echo "  $DATA_DIR"
echo ""
echo "To completely remove all data, run:"
echo "  rm -rf $DATA_DIR"
echo ""
echo "Thank you for using Seven!"
echo ""
