import sys
import os
import time
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, List, Optional, Callable

# Add holehe_OSINT to sys.path so we can import holehe components
BASE_DIR = Path(__file__).resolve().parents[4]  # /mnt/devdata/works/VivekMedha
HOLEHE_DIR = BASE_DIR / "holehe_OSINT"
if str(HOLEHE_DIR) not in sys.path:
    sys.path.insert(0, str(HOLEHE_DIR))

import httpx
import trio
from holehe.core import import_submodules, get_functions, launch_module

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

PLATFORM_CATEGORIES: Dict[str, str] = {
    # Social Networks
    "twitter": "social", "instagram": "social", "snapchat": "social", "pinterest": "social",
    "tumblr": "social", "parler": "social", "taringa": "social", "tellonym": "social",
    "quora": "social", "plurk": "social", "myspace": "social", "fanpop": "social",
    "ello": "social", "bitmoji": "social",
    # Developer & Tech
    "github": "tech", "replit": "tech", "docker": "tech", "codepen": "tech",
    "codecademy": "tech", "codeigniter": "tech", "devrant": "tech", "atlassian": "tech",
    "biosmods": "tech", "biotechnologyforums": "tech",
    # Enterprise & Productivity
    "google": "business", "office365": "business", "evernote": "business", "lastpass": "business",
    "hubspot": "business", "pipedrive": "business", "insightly": "business", "nutshell": "business",
    "zoho": "business", "axonaut": "business", "amocrm": "business", "nimble": "business",
    "nocrm": "business", "teamleader": "business", "rocketreach": "business", "xing": "business",
    "freelancer": "business",
    # Media & Creative
    "spotify": "media", "soundcloud": "media", "lastfm": "media", "imgur": "media",
    "flickr": "media", "gravatar": "media", "vsco": "media", "smule": "media",
    "blip": "media", "tunefind": "media", "archive": "media", "crevado": "media",
    "coroflot": "media",
    # E-Commerce & Delivery
    "amazon": "retail", "ebay": "retail", "deliveroo": "retail", "nike": "retail",
    "blablacar": "retail", "dominosfr": "retail", "naturabuy": "retail", "vrbo": "retail",
    "envato": "retail",
    # Communication & Gaming
    "discord": "gaming", "clashfarmer": "gaming", "badeggsonline": "gaming", "garmin": "gaming",
    "komoot": "gaming", "strava": "gaming", "onlinesequencer": "gaming", "sporcle": "gaming",
    # Adult Services
    "pornhub": "adult", "redtube": "adult", "xnxx": "adult", "xvideos": "adult",
    "babeshows": "adult",
}

def get_platform_category(name: str) -> str:
    """Categorizes platform by name."""
    clean = name.lower().replace("-", "_").replace(".", "_")
    for key, cat in PLATFORM_CATEGORIES.items():
        if key in clean or clean in key:
            return cat
    return "general"

def is_valid_email(email: str) -> bool:
    """Validates single email format."""
    return bool(re.match(EMAIL_REGEX, email.strip()))

def parse_target_emails(text: str) -> List[str]:
    """Extracts unique valid emails from multi-line or comma/space-separated strings."""
    if not text:
        return []
    tokens = re.split(r'[\r\n,;\s]+', text.strip())
    unique_emails = []
    seen = set()
    for t in tokens:
        cleaned = t.strip()
        if is_valid_email(cleaned):
            lower = cleaned.lower()
            if lower not in seen:
                seen.add(lower)
                unique_emails.append(cleaned)
    return unique_emails

async def _wrapped_launch(module, email: str, client: httpx.AsyncClient, out: list, lock: trio.Lock, total: int, callback: Optional[Callable]):
    """Wraps module launch to stream real-time progress callbacks safely."""
    await launch_module(module, email, client, out)
    if callback:
        async with lock:
            latest = out[-1] if out else None
            current = len(out)
        try:
            callback(current, total, latest)
        except Exception:
            pass

async def _run_holehe_async(
    email: str,
    timeout: int = 10,
    no_password_recovery: bool = False,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """Asynchronous engine runner executing holehe triage across target websites."""
    start_time = time.time()
    modules = import_submodules("holehe.modules")
    
    # Pass SimpleNamespace with nopasswordrecovery flag to get_functions
    args_ns = SimpleNamespace(nopasswordrecovery=no_password_recovery)
    websites = get_functions(modules, args_ns)
    total_sites = len(websites)
    
    out: List[Dict[str, Any]] = []
    lock = trio.Lock()
    
    client = httpx.AsyncClient(timeout=timeout)
    try:
        async with trio.open_nursery() as nursery:
            for site_func in websites:
                nursery.start_soon(_wrapped_launch, site_func, email, client, out, lock, total_sites, progress_callback)
    finally:
        await client.aclose()

    duration = round(time.time() - start_time, 2)
    
    # Process and classify findings and complete audit list
    findings = []
    all_services = []
    registered_count = 0
    not_registered_count = 0
    rate_limited_count = 0
    error_count = 0

    for item in out:
        name = item.get("name", "unknown")
        domain = item.get("domain", "")
        exists = item.get("exists")
        rate_limit = bool(item.get("rateLimit"))
        error = bool(item.get("error"))

        category = get_platform_category(name)
        item["category"] = category

        if exists is True:
            status = "registered"
            registered_count += 1
            entry = {
                "name": name,
                "domain": domain,
                "category": category,
                "status": "registered",
                "method": item.get("method", "register"),
                "email_recovery": item.get("emailrecovery"),
                "phone_number": item.get("phoneNumber"),
                "others": item.get("others")
            }
            findings.append(entry)
            all_services.append(entry)
        elif rate_limit:
            status = "rate_limited"
            rate_limited_count += 1
            all_services.append({
                "name": name,
                "domain": domain,
                "category": category,
                "status": "rate_limited",
                "method": item.get("method", "register"),
                "email_recovery": None,
                "phone_number": None,
                "others": None
            })
        elif error:
            status = "error"
            error_count += 1
            all_services.append({
                "name": name,
                "domain": domain,
                "category": category,
                "status": "error",
                "method": item.get("method", "register"),
                "email_recovery": None,
                "phone_number": None,
                "others": None
            })
        else:
            status = "not_registered"
            not_registered_count += 1
            all_services.append({
                "name": name,
                "domain": domain,
                "category": category,
                "status": "not_registered",
                "method": item.get("method", "register"),
                "email_recovery": None,
                "phone_number": None,
                "others": None
            })

    # Sort findings & all_services alphabetically by platform name
    findings = sorted(findings, key=lambda x: x["name"])
    all_services = sorted(all_services, key=lambda x: x["name"])

    # Extract target domain
    domain_part = email.split("@")[-1] if "@" in email else ""

    return {
        "engine": "OASIS Email Intelligence Engine",
        "version": "1.0.0",
        "system": "OASIS OSINT Suite",
        "status": "COMPLETED",
        "target": email,
        "domain": domain_part,
        "no_password_recovery": no_password_recovery,
        "total_checked": len(out),
        "total_registered": registered_count,
        "total_not_registered": not_registered_count,
        "total_rate_limited": rate_limited_count,
        "total_errors": error_count,
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "findings": findings,
        "all_services": all_services,
        "raw_results": out
    }

def execute_holehe_scan(
    email: str,
    timeout: int = 10,
    no_password_recovery: bool = False,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """Synchronous entry point that runs the Trio event loop."""
    return trio.run(_run_holehe_async, email, timeout, no_password_recovery, progress_callback)
