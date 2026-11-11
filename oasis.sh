#!/usr/bin/env bash
# ==============================================================================
# OASIS — OSINT Aggregation and Strategic Intelligence System
# Incubated at Ramakrishna Mission Vidyamandira
#
# Master Control CLI & Service Management Script
# Designed for Linux development environments and production servers.
#
# Usage:
#   ./oasis.sh [command]
#
# Commands:
#   start       Start OASIS server as a persistent background daemon
#   dev         Start OASIS in foreground with live reload (debug mode)
#   stop        Stop running OASIS instance gracefully
#   restart     Restart OASIS instance
#   status      Display running state, PID, port, URLs, and live health
#   logs        Stream live output logs (tail -f)
#   port        Show configured port and port usage
#   setup       Initialize/verify Python virtual environment & dependencies
#   help        Show this help reference
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# Configuration Defaults (overridable via environment variables or .env)
# ------------------------------------------------------------------------------
if [ -f "$SCRIPT_DIR/.env" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
fi

OASIS_HOST="${OASIS_HOST:-0.0.0.0}"
OASIS_PORT="${OASIS_PORT:-5050}"
RUN_DIR="${OASIS_RUN_DIR:-$SCRIPT_DIR/.run}"
PID_FILE="$RUN_DIR/oasis.pid"
LOG_FILE="$RUN_DIR/oasis.log"
VENV_DIR="$SCRIPT_DIR/.venv"

mkdir -p "$RUN_DIR"

# ------------------------------------------------------------------------------
# Helper: Detect Python Binary
# ------------------------------------------------------------------------------
get_python() {
    if [ -x "$VENV_DIR/bin/python3" ]; then
        echo "$VENV_DIR/bin/python3"
    elif [ -x "$VENV_DIR/bin/python" ]; then
        echo "$VENV_DIR/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        echo "$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        echo "$(command -v python)"
    else
        echo ""
    fi
}

# ------------------------------------------------------------------------------
# Helper: Check Running PID (PID file with fallback to port listener check)
# ------------------------------------------------------------------------------
get_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi

    # Fallback to lsof / fuser / ss if pid file was missing or stale
    if command -v lsof >/dev/null 2>&1; then
        local port_pid
        port_pid=$(lsof -ti tcp:"$OASIS_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)
        if [ -n "$port_pid" ]; then
            echo "$port_pid"
            return 0
        fi
    elif command -v fuser >/dev/null 2>&1; then
        local fuser_pid
        fuser_pid=$(fuser "$OASIS_PORT"/tcp 2>/dev/null | awk '{print $1}' || true)
        if [ -n "$fuser_pid" ]; then
            echo "$fuser_pid"
            return 0
        fi
    fi

    echo ""
}

# ------------------------------------------------------------------------------
# Subcommand: setup
# ------------------------------------------------------------------------------
cmd_setup() {
    echo "=================================================================="
    echo "  OASIS Environment Setup"
    echo "  Incubated at Ramakrishna Mission Vidyamandira"
    echo "=================================================================="

    local sys_py
    sys_py=$(command -v python3 || command -v python || true)
    if [ -z "$sys_py" ]; then
        echo "[!] Error: python3 is not found. Please install Python 3.10+."
        exit 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        echo "[*] Creating dedicated virtual environment (.venv)..."
        "$sys_py" -m venv "$VENV_DIR"
    else
        echo "[*] Virtual environment located: $VENV_DIR"
    fi

    local py_bin
    py_bin="$VENV_DIR/bin/python3"
    echo "[*] Installing/verifying requirements from requirements.txt..."
    "$py_bin" -m pip install --upgrade pip --quiet
    "$py_bin" -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet

    echo "[✓] Setup complete."
}

# ------------------------------------------------------------------------------
# Subcommand: start (Persistent background daemon)
# ------------------------------------------------------------------------------
cmd_start() {
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "[!] OASIS is already running (PID: $pid) on port $OASIS_PORT."
        echo "    Dashboard: http://127.0.0.1:$OASIS_PORT/dashboard"
        return 0
    fi

    local py_bin
    py_bin=$(get_python)
    if [ -z "$py_bin" ] || [ ! -x "$py_bin" ]; then
        echo "[*] Python venv missing. Running setup first..."
        cmd_setup
        py_bin=$(get_python)
    fi

    echo "[*] Starting OASIS on $OASIS_HOST:$OASIS_PORT (Daemon Mode)..."

    export OASIS_PORT="$OASIS_PORT"
    export OASIS_HOST="$OASIS_HOST"

    # Prefer start-stop-daemon if available (standard on Debian/Ubuntu/production Linux)
    if command -v start-stop-daemon >/dev/null 2>&1; then
        start-stop-daemon --start \
            --background \
            --make-pidfile \
            --pidfile "$PID_FILE" \
            --chdir "$SCRIPT_DIR" \
            --output "$LOG_FILE" \
            --startas "$py_bin" \
            -- -m uvicorn server:app --host "$OASIS_HOST" --port "$OASIS_PORT"
    else
        # Portable setsid / nohup fallback
        ( setsid "$py_bin" -m uvicorn server:app --host "$OASIS_HOST" --port "$OASIS_PORT" >> "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE" ) </dev/null
    fi

    # Verification polling (up to 5 seconds)
    local healthy=false
    local new_pid
    for _ in {1..10}; do
        sleep 0.5
        new_pid=$(get_pid)
        if [ -n "$new_pid" ]; then
            if curl -s -f "http://127.0.0.1:$OASIS_PORT/api/status" >/dev/null 2>&1; then
                healthy=true
                break
            fi
        fi
    done

    if [ "$healthy" = true ]; then
        echo "[✓] OASIS started successfully."
        echo "    • PID:       $new_pid"
        echo "    • Host:      $OASIS_HOST"
        echo "    • Port:      $OASIS_PORT"
        echo "    • Dashboard: http://127.0.0.1:$OASIS_PORT/dashboard"
        echo "    • API Docs:  http://127.0.0.1:$OASIS_PORT/docs"
        echo "    • Logs:      $LOG_FILE"
    else
        if [ -n "$new_pid" ]; then
            echo "[*] OASIS server process running (PID: $new_pid). Warming up..."
            echo "    Dashboard: http://127.0.0.1:$OASIS_PORT/dashboard"
        else
            echo "[✗] Failed to start OASIS. Recent logs:"
            tail -n 20 "$LOG_FILE" || true
            rm -f "$PID_FILE"
            return 1
        fi
    fi
}

# ------------------------------------------------------------------------------
# Subcommand: dev (Foreground with live reload)
# ------------------------------------------------------------------------------
cmd_dev() {
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "[!] OASIS is currently active (PID: $pid). Stopping background process..."
        cmd_stop
    fi

    local py_bin
    py_bin=$(get_python)
    if [ -z "$py_bin" ] || [ ! -x "$py_bin" ]; then
        cmd_setup
        py_bin=$(get_python)
    fi

    echo "[*] Starting OASIS in Foreground Dev Mode (Live Reload Enabled)..."
    echo "    Listening at: http://$OASIS_HOST:$OASIS_PORT"
    export OASIS_PORT="$OASIS_PORT"
    export OASIS_HOST="$OASIS_HOST"

    exec "$py_bin" -m uvicorn server:app \
        --host "$OASIS_HOST" \
        --port "$OASIS_PORT" \
        --reload
}

# ------------------------------------------------------------------------------
# Subcommand: stop
# ------------------------------------------------------------------------------
cmd_stop() {
    local pid
    pid=$(get_pid)

    if [ -z "$pid" ]; then
        echo "[*] OASIS is not running."
        rm -f "$PID_FILE"
        return 0
    fi

    echo "[*] Stopping OASIS (PID: $pid)..."
    kill -15 "$pid" 2>/dev/null || true

    local stopped=false
    for _ in {1..10}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            stopped=true
            break
        fi
        sleep 0.5
    done

    if [ "$stopped" = false ]; then
        echo "[!] Graceful shutdown timed out. Forcing termination (SIGKILL)..."
        kill -9 "$pid" 2>/dev/null || true
    fi

    # Clean any lingering listener on this specific port
    if command -v fuser >/dev/null 2>&1; then
        fuser -k -s "$OASIS_PORT"/tcp 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo "[✓] OASIS stopped."
}

# ------------------------------------------------------------------------------
# Subcommand: restart
# ------------------------------------------------------------------------------
cmd_restart() {
    echo "[*] Restarting OASIS..."
    cmd_stop
    sleep 1
    cmd_start
}

# ------------------------------------------------------------------------------
# Subcommand: status
# ------------------------------------------------------------------------------
cmd_status() {
    echo "=================================================================="
    echo "  OASIS — OSINT Aggregation and Strategic Intelligence System"
    echo "  Incubated at Ramakrishna Mission Vidyamandira"
    echo "=================================================================="

    local pid
    pid=$(get_pid)

    if [ -n "$pid" ]; then
        echo "  • Status:       RUNNING (Active)"
        echo "  • Process PID:  $pid"
        echo "  • Bind Address: $OASIS_HOST"
        echo "  • Active Port:  $OASIS_PORT"
        echo "  • Local URL:    http://127.0.0.1:$OASIS_PORT/dashboard"
        echo "  • Health API:   http://127.0.0.1:$OASIS_PORT/api/status"
        echo "  • Log File:     $LOG_FILE"
        echo "------------------------------------------------------------------"

        if command -v curl >/dev/null 2>&1; then
            local api_out
            api_out=$(curl -s "http://127.0.0.1:$OASIS_PORT/api/status" 2>/dev/null || true)
            if [ -n "$api_out" ]; then
                echo "  • Live Status:  $api_out"
            fi
        fi
    else
        echo "  • Status:       STOPPED (Inactive)"
        echo "  • Config Port:  $OASIS_PORT"
        echo "  • Bind Host:    $OASIS_HOST"
        echo "  • Log File:     $LOG_FILE"
        echo "------------------------------------------------------------------"
        echo "  Tip: Run './oasis.sh start' to launch OASIS."
    fi
}

# ------------------------------------------------------------------------------
# Subcommand: logs
# ------------------------------------------------------------------------------
cmd_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "[!] Log file does not exist yet ($LOG_FILE)."
        exit 0
    fi
    echo "[*] Streaming live logs from $LOG_FILE (Press Ctrl+C to exit)..."
    tail -n 50 -f "$LOG_FILE"
}

# ------------------------------------------------------------------------------
# Subcommand: port
# ------------------------------------------------------------------------------
cmd_port() {
    echo "Configured Port: $OASIS_PORT"
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "Port Status:     IN USE by OASIS (PID: $pid)"
    else
        if command -v lsof >/dev/null 2>&1; then
            local other_pid
            other_pid=$(lsof -ti tcp:"$OASIS_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)
            if [ -n "$other_pid" ]; then
                echo "Port Status:     IN USE by another process (PID: $other_pid)"
            else
                echo "Port Status:     AVAILABLE (Free)"
            fi
        elif command -v fuser >/dev/null 2>&1; then
            local fuser_pid
            fuser_pid=$(fuser "$OASIS_PORT"/tcp 2>/dev/null | awk '{print $1}' || true)
            if [ -n "$fuser_pid" ]; then
                echo "Port Status:     IN USE by process (PID: $fuser_pid)"
            else
                echo "Port Status:     AVAILABLE (Free)"
            fi
        else
            echo "Port Status:     NOT IN USE"
        fi
    fi
}

# ------------------------------------------------------------------------------
# Subcommand: help
# ------------------------------------------------------------------------------
cmd_help() {
    echo "OASIS Master Management Script"
    echo "Incubated at Ramakrishna Mission Vidyamandira"
    echo ""
    echo "Usage: ./oasis.sh <command>"
    echo ""
    echo "Commands:"
    echo "  start       Start OASIS server as a persistent background daemon"
    echo "  dev         Start OASIS in foreground with live reload (dev mode)"
    echo "  stop        Stop running OASIS instance gracefully"
    echo "  restart     Restart OASIS instance"
    echo "  status      Check state, process PID, port, URLs, and telemetry"
    echo "  logs        Stream real-time log output"
    echo "  port        Show configured port and port usage"
    echo "  setup       Setup/verify Python virtual environment & dependencies"
    echo "  help        Display this help message"
    echo ""
    echo "Environment Variables (or .env file):"
    echo "  OASIS_PORT  Listening port (default: 5050)"
    echo "  OASIS_HOST  Binding host (default: 0.0.0.0)"
}

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------
case "${1:-status}" in
    start)
        cmd_start
        ;;
    dev)
        cmd_dev
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    port)
        cmd_port
        ;;
    setup)
        cmd_setup
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        echo "[!] Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
