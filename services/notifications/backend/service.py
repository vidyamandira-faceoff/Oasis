from typing import List, Dict, Optional
from core.notifications import (
    get_tool_notifications,
    get_notification_counts,
    clear_completed_notifications
)

def list_tool_notifications(status_filter: Optional[str] = "ALL", tool_filter: Optional[str] = "ALL") -> List[Dict]:
    return get_tool_notifications(status_filter=status_filter or "ALL", tool_filter=tool_filter or "ALL")

def get_stats() -> Dict:
    return get_notification_counts()

def purge_completed_notifications():
    cleared = clear_completed_notifications()
    return {"status": "cleared", "count": cleared}
