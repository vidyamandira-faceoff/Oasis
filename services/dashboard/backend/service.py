import os
import time
from pathlib import Path
from core.config import BASE_DIR, SERVICES_DIR
from core.process_manager import RUNNING_PROCESSES

def get_dashboard_summary():
    return {
        "active_investigations": 1,
        "active_modules_count": "2 / 12",
        "connected_engines_count": "2 Ready",
        "active_engine_name": "Username Intelligence Engine",
        "system_status": "Operational",
        "compliance_tag": "DEMO BUILD — not for casework"
    }
