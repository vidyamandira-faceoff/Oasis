import time
from typing import List, Dict, Optional
from datetime import datetime

# In-memory notifications store for Oasis background recon engines & scrapers
_NOTIFICATIONS_STORE: List[Dict] = [
    {
        "id": "notif-url-01",
        "tool": "Website URL Recon",
        "tool_code": "recon_website_url",
        "status": "FINISHED",
        "status_class": "status-finished",
        "title": "Deep Endpoint Crawl Finished",
        "target": "belurmath.org",
        "details": "Multi-engine background crawling completed. Harvested 86,120 endpoints, assets, parameters, and document links.",
        "metrics": "86,120 Endpoints • 18,459 Files • 66 Fuzzable Params",
        "timestamp": "2026-11-03 12:41:00",
        "time_display": "Nov 3, 12:41 PM",
        "progress": 100,
        "action_url": "/services/recon-website-url",
        "action_label": "Inspect Output"
    },
    {
        "id": "notif-sub-01",
        "tool": "Subdomain Recon",
        "tool_code": "recon_subdomains",
        "status": "FINISHED",
        "status_class": "status-finished",
        "title": "Subdomain Enumeration Finished",
        "target": "animeschedule.net",
        "details": "DNS bruteforce and Certificate Transparency logs indexed. Discovered 14 valid hostnames and active DNS records.",
        "metrics": "14 Hostnames • 3 Nameservers • 100% Resolved",
        "timestamp": "2026-11-02 21:11:00",
        "time_display": "Nov 2, 09:11 PM",
        "progress": 100,
        "action_url": "/services/recon-subdomains",
        "action_label": "Inspect Output"
    },
    {
        "id": "notif-ig-01",
        "tool": "Instagram Intelligence",
        "tool_code": "social_instagram",
        "status": "FINISHED",
        "status_class": "status-finished",
        "title": "Instagram Profile Dossier Extracted",
        "target": "@veritasium_daily",
        "details": "Profile metadata, follower graph, hashtags, and media links successfully extracted and indexed in vault.",
        "metrics": "Indexed • Profile Bio & Post Tags",
        "timestamp": "2026-11-04 18:22:00",
        "time_display": "Nov 4, 06:22 PM",
        "progress": 100,
        "action_url": "/services/social-instagram",
        "action_label": "Open Profiler"
    },
    {
        "id": "notif-ip-01",
        "tool": "IP Intelligence",
        "tool_code": "recon_ip",
        "status": "FINISHED",
        "status_class": "status-finished",
        "title": "IP Range & ASN Audit Completed",
        "target": "104.21.55.2",
        "details": "GeoIP coordinates, autonomous system routing, reverse DNS pointers, and open port telemetry indexed.",
        "metrics": "Cloudflare ASN 13335 • US Anycast",
        "timestamp": "2026-11-05 14:15:00",
        "time_display": "Nov 5, 02:15 PM",
        "progress": 100,
        "action_url": "/services/recon-ip",
        "action_label": "View Footprint"
    },
    {
        "id": "notif-email-01",
        "tool": "Email Recon",
        "tool_code": "recon_email",
        "status": "FINISHED",
        "status_class": "status-finished",
        "title": "Email Breach & Verification Query",
        "target": "admin@targetdomain.com",
        "details": "Mailbox MX routing validated, deliverability confirmed, and public security disclosures cross-referenced.",
        "metrics": "MX Active • SPF/DKIM Valid",
        "timestamp": "2026-11-05 17:30:00",
        "time_display": "Nov 5, 05:30 PM",
        "progress": 100,
        "action_url": "/services/recon-email",
        "action_label": "Inspect Verification"
    }
]

def add_recon_notification(
    tool: str,
    status: str,
    title: str,
    details: str,
    target: str = "",
    metrics: str = "",
    action_url: str = "",
    action_label: str = "Inspect"
) -> Dict:
    """
    Registers a new notification for Oasis background recon engines.
    """
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    time_display = now.strftime("%b %d, %I:%M %p")
    notif_id = f"notif-{int(time.time()*1000)}"

    tool_code = tool.lower().replace(" ", "_")
    status_clean = status.upper()
    status_class = "status-processing" if status_clean == "PROCESSING" else "status-finished"

    item = {
        "id": notif_id,
        "tool": tool,
        "tool_code": tool_code,
        "status": status_clean,
        "status_class": status_class,
        "title": title,
        "target": target,
        "details": details,
        "metrics": metrics,
        "timestamp": timestamp_str,
        "time_display": time_display,
        "progress": 0 if status_clean == "PROCESSING" else 100,
        "action_url": action_url,
        "action_label": action_label
    }

    _NOTIFICATIONS_STORE.insert(0, item)
    return item

# Compatibility alias
add_osint_notification = add_recon_notification

def update_tool_notification(
    tool: str,
    target: str,
    new_status: str,
    title: Optional[str] = None,
    details: Optional[str] = None,
    metrics: Optional[str] = None,
    progress: Optional[int] = None
) -> Optional[Dict]:
    tool_code = tool.lower().replace(" ", "_")
    target_clean = target.strip().lower()

    for item in _NOTIFICATIONS_STORE:
        match_tool = item["tool_code"] == tool_code or tool_code in item["tool_code"]
        match_target = not target_clean or item["target"].lower() == target_clean
        if match_tool and match_target:
            item["status"] = new_status.upper()
            item["status_class"] = "status-processing" if item["status"] == "PROCESSING" else "status-finished"
            if title: item["title"] = title
            if details: item["details"] = details
            if metrics: item["metrics"] = metrics
            if progress is not None:
                item["progress"] = progress
            elif item["status"] == "FINISHED":
                item["progress"] = 100
            return item

    # If not found, create new record
    return add_recon_notification(
        tool=tool,
        status=new_status,
        title=title or f"{tool} Task {new_status.capitalize()}",
        details=details or f"Recon task update for {target or 'active process'}.",
        target=target,
        metrics=metrics or ""
    )

def get_tool_notifications(
    status_filter: str = "ALL",
    tool_filter: str = "ALL",
    limit: int = 50
) -> List[Dict]:
    filtered = []
    status_f = status_filter.upper()
    tool_f = tool_filter.lower()

    for item in _NOTIFICATIONS_STORE:
        if status_f != "ALL" and item["status"] != status_f:
            continue
        if tool_f != "ALL" and tool_f not in item["tool_code"]:
            continue
        filtered.append(item)
        if len(filtered) >= limit:
            break

    return filtered

def clear_completed_notifications() -> int:
    global _NOTIFICATIONS_STORE
    orig_len = len(_NOTIFICATIONS_STORE)
    _NOTIFICATIONS_STORE = [n for n in _NOTIFICATIONS_STORE if n["status"] == "PROCESSING"]
    return orig_len - len(_NOTIFICATIONS_STORE)

def get_notification_counts() -> Dict[str, int]:
    processing = 0
    finished = 0
    for n in _NOTIFICATIONS_STORE:
        if n["status"] == "PROCESSING":
            processing += 1
        elif n["status"] == "FINISHED":
            finished += 1
    return {
        "processing": processing,
        "finished": finished,
        "total": len(_NOTIFICATIONS_STORE),
        "badge_count": processing if processing > 0 else (1 if finished > 0 else 0)
    }
