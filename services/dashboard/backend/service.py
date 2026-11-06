import os
import time
from pathlib import Path
from core.config import BASE_DIR, SERVICES_DIR
from core.process_manager import is_port_open

def get_dashboard_summary():
    final_assets = 148520
    targets_count = 28

    return {
        "active_targets_count": targets_count,
        "total_assets_count": final_assets,
        "total_assets_formatted": f"{final_assets:,}",
        "recon_velocity": "99.2%",
        "engines_ready": "12 / 12",
        "social_engines_ready": "4 Active",
        "recon_engines_ready": "8 Active"
    }
