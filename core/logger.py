import time
from typing import List, Dict

PROCESS_LOGS: List[Dict[str, str]] = []
MAX_LOGS = 1000

def add_log(source: str, message: str, level: str = "info"):
    entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "source": source,
        "message": message.strip(),
        "level": level
    }
    PROCESS_LOGS.append(entry)
    if len(PROCESS_LOGS) > MAX_LOGS:
        PROCESS_LOGS.pop(0)

def get_logs(limit: int = 100) -> List[Dict[str, str]]:
    return PROCESS_LOGS[-limit:]

def clear_logs():
    PROCESS_LOGS.clear()

add_log("Oasis", "Oasis Modular Microservices Gateway initialized.", "success")

