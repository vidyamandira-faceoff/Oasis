import os
import sys
import signal
import socket
import subprocess
import threading
from typing import Dict, Optional
from core.logger import add_log

RUNNING_PROCESSES: Dict[str, subprocess.Popen] = {}

def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def register_process(name: str, proc: subprocess.Popen, stream_logs: bool = True):
    RUNNING_PROCESSES[name] = proc
    if stream_logs and proc.stdout:
        def stream_output():
            for line in proc.stdout:
                clean = line.strip()
                if clean:
                    add_log(name.capitalize(), clean, "info")
            proc.wait()
            add_log(name.capitalize(), f"Process ended with code {proc.returncode}", "warning" if proc.returncode != 0 else "success")
            try:
                from core.notifications import update_tool_notification
                update_tool_notification(
                    tool=name.capitalize(),
                    target="",
                    new_status="FINISHED",
                    title=f"{name.capitalize()} Processing Finished",
                    details=f"{name.capitalize()} execution finished with exit code {proc.returncode}.",
                    metrics=f"Exit Code: {proc.returncode}"
                )
            except Exception:
                pass
            if name in RUNNING_PROCESSES and RUNNING_PROCESSES[name] == proc:
                del RUNNING_PROCESSES[name]
        threading.Thread(target=stream_output, daemon=True).start()

def force_kill_tree(pid: int):
    """
    Forcefully terminates a process and all of its children across Windows, Linux and macOS.
    """
    if os.name == "nt":
        # Windows process tree force termination
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=3)
        except Exception:
            pass
    else:
        # Linux / Ubuntu / Unix process group termination
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGKILL)
            return
        except Exception:
            pass

        try:
            subprocess.run(["pkill", "-9", "-P", str(pid)], capture_output=True, timeout=2)
        except Exception:
            pass

        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

def free_port(port: int):
    """
    Releases any listening socket on the specified port across Windows, Linux and macOS.
    """
    if os.name == "nt":
        # Windows netstat check
        try:
            res = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
            for line in res.stdout.strip().splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True, timeout=3)
        except Exception:
            pass
    else:
        # Linux / Ubuntu / macOS port liberation
        try:
            # fuser is standard on Ubuntu/Debian/RHEL
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=2)
        except Exception:
            pass

        try:
            # lsof fallback
            cmd = f"lsof -ti:{port} | xargs -r kill -9"
            subprocess.run(cmd, shell=True, capture_output=True, timeout=2)
        except Exception:
            pass

def terminate_process(name: str, port: Optional[int] = None) -> bool:
    name = name.lower()
    killed = False
    
    # 1. Kill registered Popen handle and its entire child process tree
    if name in RUNNING_PROCESSES:
        proc = RUNNING_PROCESSES[name]
        try:
            force_kill_tree(proc.pid)
            proc.kill()
        except Exception:
            pass
        del RUNNING_PROCESSES[name]
        killed = True

    # 2. If a port is bound, ensure it is released immediately
    if port:
        free_port(port)
        killed = True

    add_log("Oasis", f"Immediately stopped tasks for engine: {name.upper()}.", "warning")
    return killed

def terminate_all_tasks() -> Dict[str, bool]:
    results = {}
    for name in list(RUNNING_PROCESSES.keys()):
        results[name] = terminate_process(name)
    free_port(8000)
    free_port(5001)
    add_log("Oasis", "Emergency abort executed: All active tools and tasks stopped immediately.", "warning")
    return results

def get_process(name: str) -> Optional[subprocess.Popen]:
    return RUNNING_PROCESSES.get(name)

def is_tool_busy(name: str) -> bool:
    return name in RUNNING_PROCESSES and RUNNING_PROCESSES[name].poll() is None

def spawn_subprocess(cmd: list, cwd: str) -> subprocess.Popen:
    """
    Helper to launch a child process with proper process group / session isolation
    so it can be reliably terminated without zombie processes on both Windows and Linux.
    """
    kwargs = {
        "cwd": cwd,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1,
        "universal_newlines": True
    }
    
    if os.name != "nt":
        # On Linux/macOS, create a new process group session so os.killpg can terminate all child threads
        kwargs["start_new_session"] = True

    return subprocess.Popen(cmd, **kwargs)
