#!/usr/bin/env bash
# ==============================================================================
# Oasis OSINT Suite — Linux & Ubuntu Launcher
# Compatible with Ubuntu, Debian, Fedora, Arch Linux, macOS and Unix environments
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "==================================================="
echo "           OASIS UNIFIED OSINT SUITE"
echo "           Linux / Ubuntu Environment"
echo "==================================================="

# 1. Determine Python 3 binary
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    echo "[!] Error: Python 3 is not installed or not in PATH."
    echo "    On Ubuntu/Debian, install with: sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

echo "[*] Using Python: $($PY_BIN --version)"

# 2. Virtual Environment check (optional, automatic if desired)
if [ -d "$DIR/.venv" ]; then
    echo "[*] Activating virtual environment (.venv)..."
    source "$DIR/.venv/bin/activate"
fi

# 3. Check / Install requirements if needed
if ! $PY_BIN -c "import fastapi, uvicorn, jinja2, requests" >/dev/null 2>&1; then
    echo "[*] Installing missing dependencies from requirements.txt..."
    $PY_BIN -m pip install -r requirements.txt --quiet || {
        echo "[!] Warning: pip install failed. If using an externally-managed environment on Ubuntu 24.04+:"
        echo "    Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    }
fi

# 4. Open default browser
PORT=${OASIS_PORT:-5050}
URL="http://127.0.0.1:${PORT}"
echo "[*] Launching browser at: $URL"

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    open "$URL" >/dev/null 2>&1 &
elif command -v sensible-browser >/dev/null 2>&1; then
    sensible-browser "$URL" >/dev/null 2>&1 &
else
    echo "[*] Note: Please open $URL manually in your web browser."
fi

# 5. Launch Oasis Gateway Server
echo "[*] Starting Oasis Gateway Server..."
exec $PY_BIN server.py

