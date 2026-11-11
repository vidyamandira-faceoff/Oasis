import os
import time
from pathlib import Path
from core.config import BASE_DIR, SERVICES_DIR
from core.process_manager import RUNNING_PROCESSES

def get_dashboard_summary():
    return {
        "active_investigations": 1,
        "active_modules_count": "4 Active",
        "connected_engines_count": "4 Ready",
        "active_engine_name": "OASIS Reconnaissance Platform",
        "system_status": "Operational",
        "compliance_tag": "PRODUCTION BUILD"
    }
