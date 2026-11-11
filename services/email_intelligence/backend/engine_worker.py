import sys
import os
import time
import re
from datetime import datetime
from pathlib import Path
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
    """Validates email format."""
    return bool(re.match(EMAIL_REGEX, email.strip()))

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
    categories: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """Asynchronous engine runner executing holehe triage across target websites."""
    start_time = time.time()
    modules = import_submodules("holehe.modules")
    websites = get_functions(modules)
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
    
    # Process and classify findings
    findings = []
    registered_count = 0
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
            registered_count += 1
            findings.append({
                "name": name,
                "domain": domain,
                "category": category,
                "method": item.get("method", "register"),
                "email_recovery": item.get("emailrecovery"),
                "phone_number": item.get("phoneNumber"),
                "others": item.get("others")
            })
        elif rate_limit:
            rate_limited_count += 1
        elif error:
            error_count += 1

    # Sort findings alphabetically by name
    findings = sorted(findings, key=lambda x: x["name"])

    # Extract target domain
    domain_part = email.split("@")[-1] if "@" in email else ""

    return {
        "engine": "OASIS Email Intelligence Engine",
        "version": "1.0.0",
        "system": "OASIS OSINT Suite",
        "status": "COMPLETED",
        "target": email,
        "domain": domain_part,
        "total_checked": len(out),
        "total_registered": registered_count,
        "total_rate_limited": rate_limited_count,
        "total_errors": error_count,
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "findings": findings,
        "raw_results": out
    }

def execute_holehe_scan(
    email: str,
    timeout: int = 10,
    categories: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int, int, Optional[Dict[str, Any]]], None]] = None
) -> Dict[str, Any]:
    """Synchronous entry point that runs the Trio event loop."""
    return trio.run(_run_holehe_async, email, timeout, categories, progress_callback)
