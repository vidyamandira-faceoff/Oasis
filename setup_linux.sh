#!/usr/bin/env bash
# ==============================================================================
# Oasis OSINT Suite — Automated Linux Setup Script
# Configures Python virtual environment, dependencies & permissions
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "==================================================="
echo "    Oasis OSINT Suite — Linux Installation"
echo "==================================================="

# 1. Package manager detection for system packages
if command -v apt-get >/dev/null 2>&1; then
    echo "[*] Debian/Ubuntu detected. Checking essential utilities..."
    MISSING_PKGS=""
    for pkg in python3 python3-pip python3-venv psmisc lsof; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS $pkg"
        fi
    done
    if [ -n "$MISSING_PKGS" ]; then
        echo "[*] Installing missing system packages:$MISSING_PKGS"
        sudo apt-get update -y
        sudo apt-get install -y $MISSING_PKGS
    fi
fi

# 2. Virtual environment setup
if [ ! -d "$DIR/.venv" ]; then
    echo "[*] Creating dedicated Python virtual environment (.venv)..."
    python3 -m venv "$DIR/.venv"
fi

echo "[*] Activating virtual environment..."
source "$DIR/.venv/bin/activate"

# 3. Upgrade pip and install Oasis requirements
echo "[*] Installing Python packages from requirements.txt..."
pip install --upgrade pip --quiet
pip install -r "$DIR/requirements.txt" --quiet

# 4. Make scripts executable
chmod +x "$DIR/run_oasis.sh" || true
chmod +x "$DIR/setup_linux.sh" || true

echo ""
echo "==================================================="
echo "  Setup Complete! Oasis is ready on Linux."
echo "  Run: ./run_oasis.sh"
echo "==================================================="

