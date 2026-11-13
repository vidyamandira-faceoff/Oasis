import os
import sys
import time
import json
import re
import uuid
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.config import BASE_DIR
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification
from services.social_media_intelligence.backend.twitter_worker import (
    scrape_twitter,
    sanitize_x_target,
    get_accounts_pool_info,
    add_session_cookies_to_pool
)
from services.social_media_intelligence.backend.linkedin_worker import (
    scrape_linkedin_workforce,
    clean_company_name
)

# Reports and Output Storage Directory
REPORTS_DIR = BASE_DIR / "services" / "social_media_intelligence" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RECON_DIR = BASE_DIR / "services" / "recon_username" / "reports"

# Engine Python interpreter (use maigret venv which has rich social registry)
def _get_social_engine_python() -> str:
    for folder in ["maigret", "maigret_osint"]:
        cand = BASE_DIR.parent / folder / ".venv" / "bin" / "python"
        if cand.exists():
            return str(cand)
    cand2 = BASE_DIR / ".venv" / "bin" / "python"
    if cand2.exists():
        return str(cand2)
    return sys.executable

MAIGRET_DIR = (BASE_DIR.parent / "maigret").resolve()
if not MAIGRET_DIR.exists():
    MAIGRET_DIR = (BASE_DIR.parent / "maigret_osint").resolve()
ENGINE_PYTHON = _get_social_engine_python()

# Native Vidyamandira Scraper Cluster URLs (Max Mode)
NATIVE_SCRAPER_ENDPOINTS = {
    "instagram": {
        "name": "Instagram Native Scraper",
        "url": "http://instagramintel.rkmvcse.in/",
        "icon": "instagram",
        "color": "#e1306c",
        "description": "Vidyamandira custom high-capacity Instagram intelligence engine with session resilience and post/follower archival."
    },
    "facebook": {
        "name": "Facebook Native Scraper",
        "url": "https://fbintel.rkmvcse.in/",
        "icon": "facebook",
        "color": "#1877f2",
        "description": "Dedicated Facebook OSINT crawler for public pages, profile metadata, engagement analysis, and community mapping."
    },
    "x": {
        "name": "X (Twitter) Native Scraper",
        "url": "http://xintel.rkmvcse.in/",
        "icon": "twitter",
        "color": "#000000",
        "description": "High-velocity X/Twitter real-time crawler, tweet harvester, timeline analyst, and mention network mapper."
    },
    "linkedin": {
        "name": "LinkedIn Intelligence Cluster",
        "url": "https://www.linkedin.com/",
        "icon": "linkedin",
        "color": "#0a66c2",
        "description": "Corporate identity, career timeline, and professional affiliation extraction cluster."
    }
}

_TASKS: Dict[str, Dict[str, Any]] = {}
_CACHED_RESULTS: Dict[str, Dict[str, Any]] = {}
_SUBPROCESSES: Dict[str, subprocess.Popen] = {}
_RUNNING_LOCK = threading.Lock()

def sanitize_text(text: str) -> str:
    """Removes any internal tool branding and replaces with OASIS terminology."""
    if not text:
        return ""
    cleaned = re.sub(r'(?i)maigret', 'Social Media Intelligence Engine', text)
    cleaned = re.sub(r'(?i)photon', 'Domain Reconnaissance Engine', cleaned)
    return cleaned

def _safe_task_dict(t: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures task dictionary is strictly JSON serializable with no internal locks/objects."""
    return {
        "target": t.get("target", ""),
        "status": t.get("status", "IDLE"),
        "mode": t.get("mode", "pro"),
        "cached": bool(t.get("cached", False)),
        "duration": t.get("duration", 0),
        "elapsed": t.get("elapsed", 0),
        "total_sites": t.get("total_sites", 100),
        "discovered_count": t.get("discovered_count", 0),
        "discovered_items": t.get("discovered_items", [])[-8:],
        "findings": t.get("findings", []),
        "stats": t.get("stats", {}),
        "progress_msg": t.get("progress_msg", ""),
        "error": t.get("error")
    }

def load_cached_report_from_disk(target: str) -> Optional[Dict[str, Any]]:
    """Loads previous social media findings from JSON report, checking local and sibling caches."""
    clean_target = target.strip()
    json_path = REPORTS_DIR / f"report_{clean_target}_simple.json"
    if not json_path.exists() and RECON_DIR.exists():
        cand = RECON_DIR / f"report_{clean_target}_simple.json"
        if cand.exists():
            json_path = cand

    if not json_path.exists():
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return _normalize_report_dict(clean_target, raw_data)
    except Exception as e:
        add_log("Social Media Intelligence", f"Failed reading cached report for {clean_target}: {e}", "warning")
        return None

def _normalize_report_dict(target: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms raw engine report into structured OASIS Social Intelligence findings."""
    findings = []
    enriched_count = 0
    unique_tags = set()

    for site_name, item in raw_data.items():
        if not isinstance(item, dict):
            continue

        status_str = str(item.get("status", "")).lower()
        if "claimed" not in status_str and "found" not in status_str and not item.get("url_user"):
            continue

        profile_url = item.get("url_user") or item.get("url_main") or ""
        tags = item.get("tags") or ["social"]
        for t in tags:
            unique_tags.add(str(t).lower())

        ids = item.get("ids") or {}
        fullname = ids.get("fullname") or ids.get("name") or ids.get("real_name") or ""
        bio = ids.get("bio") or ids.get("description") or ids.get("about") or ""
        avatar = ids.get("image") or ids.get("avatar") or ids.get("profile_pic") or ""
        location = ids.get("location") or ids.get("country") or ids.get("city") or ""
        followers = ids.get("follower_count") or ids.get("followers") or ""
        following = ids.get("following_count") or ids.get("following") or ""
        created_at = ids.get("created_at") or ids.get("registration_date") or ""

        outbound_links = []
        for k, v in ids.items():
            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                if v != profile_url and v != avatar:
                    outbound_links.append(v)

        is_enriched = bool(fullname or bio or avatar or location or outbound_links)
        if is_enriched:
            enriched_count += 1

        alexa_rank = item.get("rank") or 99999

        findings.append({
            "platform": site_name,
            "url": profile_url,
            "status": "Claimed",
            "alexa_rank": alexa_rank,
            "tags": [str(t) for t in tags if t],
            "fullname": str(fullname).strip() if fullname and fullname != "—" else "",
            "bio": str(bio).strip() if bio else "",
            "avatar": str(avatar).strip() if avatar else "",
            "location": str(location).strip() if location else "",
            "followers": str(followers) if followers else "",
            "following": str(following) if following else "",
            "created_at": str(created_at).strip() if created_at else "",
            "links": outbound_links[:5],
            "raw_metadata": {k: v for k, v in ids.items() if not k.startswith("_")}
        })

    # Sort: high priority social platforms first
    priority_order = ["instagram", "facebook", "twitter", "x", "linkedin", "tiktok", "youtube", "reddit", "telegram"]
    def get_sort_key(f):
        plat = f["platform"].lower()
        for idx, p in enumerate(priority_order):
            if p in plat:
                return (0, idx)
        return (1, 0 if (f["bio"] or f["fullname"]) else 2)

    findings.sort(key=get_sort_key)

    return {
        "target": target,
        "total_claimed": len(findings),
        "enriched_count": enriched_count,
        "tags": sorted(list(unique_tags)),
        "findings": findings,
        "files": {
            "json": str(REPORTS_DIR / f"report_{target}_simple.json"),
            "csv": str(REPORTS_DIR / f"report_{target}.csv")
        }
    }

def _run_social_worker(target: str, mode: str, platform_filter: str):
    """Background worker executing the multi-mode social intelligence engine."""
    clean_target = target.strip()
    task_info = _TASKS[clean_target]

    cmd = [
        ENGINE_PYTHON,
        "-c",
        "import sys; from maigret.maigret import run; run()",
        clean_target,
        "--folderoutput", str(REPORTS_DIR),
        "-J", "simple",
        "-C",
        "-T",
        "--tags", "social,messaging,streaming,photo,video,forum,networking",
        "--no-color",
        "--no-progressbar",
        "--no-autoupdate",
    ]

    # Mode configuration
    if mode == "flash":
        cmd.extend(["--top-sites", "100", "--timeout", "4", "-n", "50"])
    elif mode == "ultra":
        cmd.extend(["-a", "--timeout", "8", "-n", "35", "--enrich", "--with-domains"])
    else:  # pro (default)
        cmd.extend(["--top-sites", "500", "--timeout", "6", "-n", "40", "--enrich"])

    if platform_filter and platform_filter != "all":
        # Target specific platform
        cmd.extend(["--site", platform_filter])

    add_log("Social Media Intelligence", f"Launching social media intelligence for handle: {clean_target} (Mode: {mode.upper()})", "info")
    add_recon_notification(
        tool="Social Media Intelligence",
        status="PROCESSING",
        title="Social Media Intelligence Initiated",
        details=f"Probing global social ecosystems for handle: {clean_target} in {mode.upper()} mode.",
        target=clean_target,
        action_url=f"/services/social-media-intelligence?target={clean_target}"
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR)
        )
        _SUBPROCESSES[clean_target] = proc

        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            line_str = line.strip()

            if "Starting a search on top" in line_str:
                parts = line_str.split("top ")
                if len(parts) > 1:
                    try:
                        num = int(parts[1].split()[0])
                        task_info["total_sites"] = num
                    except Exception:
                        pass
                task_info["progress_msg"] = sanitize_text(line_str)

            elif line_str.startswith("[+]") and ":" in line_str and not "Using sites" in line_str:
                content = line_str[3:].strip()
                tokens = content.split(":", 1)
                if len(tokens) == 2:
                    p_name = tokens[0].strip()
                    p_url = tokens[1].strip()
                    task_info["discovered_count"] += 1
                    task_info["discovered_items"].append({
                        "platform": p_name,
                        "url": p_url
                    })
                    task_info["progress_msg"] = f"Claimed profile identified on {p_name}"

        proc.wait()

        # Parse saved report
        report_file = REPORTS_DIR / f"report_{clean_target}_simple.json"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
            normalized = _normalize_report_dict(clean_target, raw_json)
        else:
            normalized = {
                "target": clean_target,
                "total_claimed": len(task_info["discovered_items"]),
                "enriched_count": 0,
                "tags": ["social"],
                "findings": [
                    {
                        "platform": item["platform"],
                        "url": item["url"],
                        "status": "Claimed",
                        "alexa_rank": 99999,
                        "tags": ["social"],
                        "fullname": "",
                        "bio": "",
                        "avatar": "",
                        "location": "",
                        "followers": "",
                        "following": "",
                        "created_at": "",
                        "links": [],
                        "raw_metadata": {}
                    }
                    for item in task_info["discovered_items"]
                ],
                "files": {}
            }

        _CACHED_RESULTS[clean_target] = normalized
        task_info["findings"] = normalized["findings"]
        task_info["stats"] = {
            "total_claimed": normalized["total_claimed"],
            "enriched_count": normalized["enriched_count"],
            "tags": normalized["tags"],
            "total_checked": task_info.get("total_sites", 500)
        }
        task_info["status"] = "COMPLETED"
        task_info["duration"] = round(time.time() - task_info["start_time"], 1)
        task_info["progress_msg"] = f"Social intelligence completed. {normalized['total_claimed']} verified accounts indexed."

        update_tool_notification(
            tool="Social Media Intelligence",
            target=clean_target,
            new_status="FINISHED",
            title="Social Media Intelligence Completed",
            details=f"Harvested {normalized['total_claimed']} verified social profiles ({normalized['enriched_count']} enriched with metadata).",
            metrics=f"{normalized['total_claimed']} Profiles • {normalized['enriched_count']} Enriched"
        )
        add_log("Social Media Intelligence", f"Completed social reconnaissance for {clean_target}: {normalized['total_claimed']} profiles found in {task_info['duration']}s.", "success")

    except Exception as e:
        task_info["status"] = "ERROR"
        task_info["error"] = sanitize_text(str(e))
        task_info["duration"] = round(time.time() - task_info["start_time"], 1)
        add_log("Social Media Intelligence", f"Error during social intelligence execution: {e}", "error")
        update_tool_notification(
            tool="Social Media Intelligence",
            target=clean_target,
            new_status="FINISHED",
            title="Social Media Intelligence Error",
            details=sanitize_text(str(e))
        )
    finally:
        _SUBPROCESSES.pop(clean_target, None)

def execute_social_task(
    target: str,
    mode: str = "pro",
    platform: str = "all",
    force: bool = False
) -> Dict[str, Any]:
    """Initiates or retrieves a Social Media Intelligence task."""
    clean_target = target.strip()
    if not clean_target:
        raise ValueError("Target username or handle cannot be empty.")

    # Max mode returns native scraper cluster redirection descriptor
    if mode.lower() == "max":
        return {
            "target": clean_target,
            "status": "MAX_REDIRECT_REQUIRED",
            "mode": "max",
            "message": "Max Mode utilizes the dedicated Vidyamandira Native High-Capacity Scraper Cluster.",
            "native_endpoints": NATIVE_SCRAPER_ENDPOINTS,
            "stats": {},
            "findings": []
        }

    # If force re-run requested, remove cache
    if force:
        json_path = REPORTS_DIR / f"report_{clean_target}_simple.json"
        csv_path = REPORTS_DIR / f"report_{clean_target}.csv"
        for p in [json_path, csv_path]:
            if p.exists():
                try: p.unlink()
                except Exception: pass
        _CACHED_RESULTS.pop(clean_target, None)
        _TASKS.pop(clean_target, None)
    else:
        cached = load_cached_report_from_disk(clean_target)
        if cached:
            _CACHED_RESULTS[clean_target] = cached
            return {
                "status": "COMPLETED",
                "cached": True,
                "target": clean_target,
                "mode": mode,
                "duration": 0.1,
                "total_sites": 500,
                "discovered_count": cached["total_claimed"],
                "stats": {
                    "total_claimed": cached["total_claimed"],
                    "enriched_count": cached["enriched_count"],
                    "tags": cached["tags"],
                    "total_checked": 500
                },
                "findings": cached["findings"],
                "progress_msg": f"Loaded {cached['total_claimed']} cached social findings from local storage."
            }

    with _RUNNING_LOCK:
        if clean_target in _TASKS and _TASKS[clean_target].get("status") == "RUNNING":
            return _safe_task_dict(_TASKS[clean_target])

        task_record = {
            "target": clean_target,
            "status": "RUNNING",
            "mode": mode,
            "cached": False,
            "start_time": time.time(),
            "duration": 0,
            "total_sites": 100 if mode == "flash" else (3000 if mode == "ultra" else 500),
            "discovered_count": 0,
            "discovered_items": [],
            "findings": [],
            "progress_msg": f"Initiating social intelligence engine ({mode.upper()} mode)...",
            "stats": {},
            "error": None
        }
        _TASKS[clean_target] = task_record

        worker = threading.Thread(
            target=_run_social_worker,
            args=(clean_target, mode, platform),
            daemon=True
        )
        worker.start()

        return _safe_task_dict(task_record)

def get_social_status(target: str) -> Dict[str, Any]:
    """Retrieves live or cached status for a target handle."""
    clean_target = target.strip()
    if clean_target in _TASKS:
        t = _TASKS[clean_target]
        elapsed = round(time.time() - t["start_time"], 1) if t["status"] == "RUNNING" else t.get("duration", 0)
        return {
            "target": clean_target,
            "status": t["status"],
            "mode": t.get("mode", "pro"),
            "cached": bool(t.get("cached", False)),
            "elapsed": elapsed,
            "total_sites": t.get("total_sites", 500),
            "discovered_count": t.get("discovered_count", 0),
            "discovered_items": t.get("discovered_items", [])[-8:],
            "progress_msg": t.get("progress_msg", ""),
            "findings": t.get("findings", []),
            "stats": t.get("stats", {}),
            "error": t.get("error")
        }

    cached = _CACHED_RESULTS.get(clean_target) or load_cached_report_from_disk(clean_target)
    if cached:
        return {
            "target": clean_target,
            "status": "COMPLETED",
            "mode": "pro",
            "cached": True,
            "elapsed": 0,
            "total_sites": 500,
            "discovered_count": cached["total_claimed"],
            "discovered_items": [],
            "progress_msg": f"Loaded {cached['total_claimed']} cached findings from local storage.",
            "findings": cached["findings"],
            "stats": {
                "total_claimed": cached["total_claimed"],
                "enriched_count": cached["enriched_count"],
                "tags": cached["tags"],
                "total_checked": 500
            },
            "error": None
        }

    return {
        "target": clean_target,
        "status": "IDLE",
        "mode": "pro",
        "cached": False,
        "elapsed": 0,
        "total_sites": 500,
        "discovered_count": 0,
        "discovered_items": [],
        "progress_msg": "Ready to scan.",
        "findings": [],
        "stats": {},
        "error": None
    }

def get_social_history() -> List[Dict[str, Any]]:
    """Returns past social investigations sorted chronologically."""
    history = []
    if not REPORTS_DIR.exists():
        return history

    for json_file in REPORTS_DIR.glob("report_*_simple.json"):
        filename = json_file.name
        prefix = "report_"
        suffix = "_simple.json"
        if filename.startswith(prefix) and filename.endswith(suffix):
            target = filename[len(prefix):-len(suffix)]
            if not target:
                continue

            try:
                stat = json_file.stat()
                mtime = stat.st_mtime
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                count = 0
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        count = len(data)

                csv_file = REPORTS_DIR / f"report_{target}.csv"
                history.append({
                    "target": target,
                    "count": count,
                    "timestamp": time_str,
                    "mtime": mtime,
                    "has_csv": csv_file.exists()
                })
            except Exception:
                pass

    history.sort(key=lambda x: x["mtime"], reverse=True)
    return history

def ensure_social_report_file(target: str, fmt: str):
    """Ensures that the requested report format (CSV, JSON, MD, TXT) exists for the social target."""
    clean_target = target.strip()
    fmt = fmt.lower().strip()

    cached = load_cached_report_from_disk(clean_target)
    if not cached or not cached.get("findings"):
        return None

    if fmt == "csv":
        p = REPORTS_DIR / f"report_{clean_target}.csv"
        if p.exists():
            return p
        import csv
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Target Handle", "Platform", "Verified Profile URL", "Fullname", "Bio", "Location", "Followers", "Category/Tags"])
            for itm in cached["findings"]:
                writer.writerow([
                    clean_target,
                    itm.get("platform", ""),
                    itm.get("url", ""),
                    itm.get("fullname", ""),
                    itm.get("bio", ""),
                    itm.get("location", ""),
                    itm.get("followers", ""),
                    "; ".join(itm.get("tags", []))
                ])
        return p

    elif fmt == "md":
        p = REPORTS_DIR / f"report_{clean_target}.md"
        if p.exists():
            return p
        md_lines = [
            f"# OASIS Social Media Intelligence Dossier: `{clean_target}`",
            "",
            f"- **Target Handle:** `{clean_target}`",
            f"- **Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Claimed Profiles:** {cached.get('total_claimed', len(cached['findings']))}",
            f"- **Enriched Profiles:** {cached.get('enriched_count', 0)}",
            "",
            "## Verified Social Media Profiles",
            ""
        ]
        for itm in cached["findings"]:
            md_lines.append(f"### {itm.get('platform')}")
            md_lines.append(f"- **URL:** [{itm.get('url')}]({itm.get('url')})")
            if itm.get("fullname"): md_lines.append(f"- **Name:** {itm.get('fullname')}")
            if itm.get("bio"): md_lines.append(f"- **Bio:** {itm.get('bio')}")
            if itm.get("location"): md_lines.append(f"- **Location:** {itm.get('location')}")
            if itm.get("followers"): md_lines.append(f"- **Followers:** {itm.get('followers')}")
            md_lines.append("")
        p.write_text("\n".join(md_lines), encoding="utf-8")
        return p

    elif fmt == "txt":
        p = REPORTS_DIR / f"report_{clean_target}.txt"
        if p.exists():
            return p
        txt_lines = [
            f"=== OASIS SOCIAL MEDIA INTELLIGENCE DOSSIER ===",
            f"Target: {clean_target}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Claimed Profiles: {cached.get('total_claimed', len(cached['findings']))}",
            "",
            "--- CLAIMED SOCIAL ACCOUNTS ---"
        ]
        for itm in cached["findings"]:
            txt_lines.append(f"[{itm.get('platform')}] {itm.get('url')}")
            if itm.get('fullname'): txt_lines.append(f"  Name: {itm.get('fullname')}")
            if itm.get('bio'): txt_lines.append(f"  Bio: {itm.get('bio')}")
        p.write_text("\n".join(txt_lines), encoding="utf-8")
        return p

    else:  # json
        p = REPORTS_DIR / f"report_{clean_target}_simple.json"
        if p.exists():
            return p
        with open(p, "w", encoding="utf-8") as f:
            raw_dict = {
                itm.get("platform"): {
                    "url_user": itm.get("url"),
                    "status": {"ids": itm.get("raw_metadata", {})}
                }
                for itm in cached["findings"]
            }
            json.dump(raw_dict, f, indent=2)
        return p


# -----------------------------------------------------------------------------
# OASIS Instagram Intelligence Engine (Flash Mode: Local / Pro Mode: Cluster)
# Fully Rebranded to OASIS OSINT Suite
# -----------------------------------------------------------------------------
INSTAGRAM_ENGINE_DIR = (BASE_DIR.parent / "instagram-scraper_OSINT").resolve()
INSTAGRAM_ENGINE_SCRIPT = INSTAGRAM_ENGINE_DIR / "engine_scraper.js"
NODE_BIN = "/usr/bin/node" if Path("/usr/bin/node").exists() else "node"

_IG_TASKS: Dict[str, Dict[str, Any]] = {}
_IG_CACHED_RESULTS: Dict[str, Dict[str, Any]] = {}
_IG_LOCK = threading.Lock()

def _sanitize_ig_key(target: str) -> str:
    cleaned = target.strip().replace("@", "")
    if "instagram.com/" in cleaned:
        cleaned = cleaned.split("instagram.com/")[-1].strip("/").replace("/", "_")
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned)

def generate_instagram_media_zip(clean_target: str, data: Dict[str, Any]) -> Optional[Path]:
    """Downloads all harvested media thumbnails and avatars into an offline OASIS ZIP archive."""
    import urllib.request
    import zipfile

    zip_path = REPORTS_DIR / f"instagram_{clean_target}_media.zip"
    posts = data.get("posts", [])
    profile = data.get("profile", {})

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.instagram.com/"
    }

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add metadata file
            meta_json = json.dumps(data, indent=2)
            zf.writestr("OASIS_metadata.json", meta_json)

            # Download avatar
            avatar_url = profile.get("avatar")
            if avatar_url and avatar_url.startswith("http"):
                try:
                    req = urllib.request.Request(avatar_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        zf.writestr("avatar_profile.jpg", resp.read())
                except Exception:
                    pass

            # Download post images
            for idx, p in enumerate(posts, 1):
                thumb = p.get("thumbnail") or p.get("display_url")
                if thumb and thumb.startswith("http"):
                    try:
                        req = urllib.request.Request(thumb, headers=headers)
                        with urllib.request.urlopen(req, timeout=12) as resp:
                            shortcode = p.get("shortcode") or f"post_{idx}"
                            ext = "jpg"
                            zf.writestr(f"media_{idx:02d}_{shortcode}.{ext}", resp.read())
                    except Exception:
                        pass

        add_log("OASIS Instagram Engine", f"Compiled offline media archive: {zip_path.name}", "success")
        return zip_path
    except Exception as e:
        add_log("OASIS Instagram Engine", f"Failed building media ZIP archive: {e}", "warning")
        return None

def _save_instagram_dossier_files(clean_target: str, data: Dict[str, Any]):
    """Persists JSON, Markdown, and CSV dossiers with full OASIS branding."""
    json_path = REPORTS_DIR / f"instagram_{clean_target}.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        add_log("OASIS Instagram Engine", f"Failed saving JSON report: {e}", "warning")

    profile = data.get("profile", {})
    posts = data.get("posts", [])
    stats = data.get("stats", {})

    # Generate OASIS Markdown report
    try:
        md_path = REPORTS_DIR / f"instagram_{clean_target}.md"
        md_lines = [
            f"# OASIS Intelligence Dossier: Instagram Reconnaissance",
            f"**Platform:** OASIS OSINT Platform | **Engine:** OASIS Instagram Intelligence Engine",
            f"**Subject Identifier:** `@{profile.get('username', clean_target)}`",
            f"**Investigation Timestamp:** {data.get('timestamp')}",
            "",
            "---",
            "",
            "## 1. Subject Profile & Identity Overview",
            "",
            f"- **Username / Handle:** `@{profile.get('username', clean_target)}`",
            f"- **Full Declared Name:** {profile.get('full_name', 'N/A')}",
            f"- **Account Verification:** {'[VERIFIED] Official Blue Badge Confirmed' if profile.get('is_verified') else 'Unverified / Standard User'}",
            f"- **Visibility Status:** {stats.get('account_status', 'Public Active')}",
            f"- **Audience Reach:** {profile.get('followers_str', 'N/A')} Followers ({profile.get('followers_count', 0):,} estimated)",
            f"- **Outbound Connections:** {profile.get('following_str', 'N/A')} Following",
            f"- **Total Account Posts:** {profile.get('posts_str', 'N/A')}",
            f"- **Biography / Bio:** {profile.get('biography') or 'No public biography supplied'}",
            f"- **Profile URL:** [{profile.get('profile_url')}]({profile.get('profile_url')})",
            f"- **Harvested Artifacts:** {len(posts)} media items | {stats.get('total_comments', 0)} comments extracted",
            "",
            "---",
            "",
            f"## 2. Harvested Media Artifacts & Posts ({len(posts)})",
            ""
        ]

        for idx, p in enumerate(posts, 1):
            shortcode = p.get('shortcode', 'N/A')
            kind = p.get('type', 'post').upper()
            md_lines.append(f"### Artifact #{idx} — {kind} (`#{shortcode}`)")
            md_lines.append(f"- **Direct Link:** [{p.get('url')}]({p.get('url')})")
            if p.get('caption'):
                md_lines.append(f"- **Caption Text:** {p.get('caption')}")
            if p.get('thumbnail'):
                md_lines.append(f"- **CDN Preview:** [View Thumbnail Asset]({p.get('thumbnail')})")
            
            comments = p.get('comments', [])
            if comments:
                md_lines.append(f"- **Extracted Comments ({len(comments)}):**")
                for c in comments:
                    author = c.get('author', 'Anonymous')
                    ctime = c.get('time', '')
                    raw_c_text = str(c.get('text', '')).replace('\n', ' ')
                    md_lines.append(f"  - **@{author}** ({ctime}): {raw_c_text}")
            md_lines.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
    except Exception as e:
        add_log("OASIS Instagram Engine", f"Failed saving MD report: {e}", "warning")

    # Generate OASIS CSV report
    try:
        csv_path = REPORTS_DIR / f"instagram_{clean_target}.csv"
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["OASIS_Index", "Target_Handle", "Media_Type", "Shortcode", "Post_URL", "Thumbnail_URL", "Comments_Count", "Caption_Snippet"])
            for idx, p in enumerate(posts, 1):
                writer.writerow([
                    idx,
                    clean_target,
                    p.get("type", "post"),
                    p.get("shortcode", ""),
                    p.get("url", ""),
                    p.get("thumbnail", ""),
                    p.get("comments_count", 0),
                    p.get("caption", "").replace("\n", " ")[:300]
                ])
    except Exception as e:
        add_log("OASIS Instagram Engine", f"Failed saving CSV report: {e}", "warning")

def _run_instagram_flash_worker(clean_target: str, count: int, session: str, target_type: str = "user", comments: bool = False, proxy: str = "", download_zip: bool = False):
    """Background worker executing the OASIS Headless Chromium Instagram Scraper."""
    task = _IG_TASKS[clean_target]
    out_file = REPORTS_DIR / f"instagram_{clean_target}.json"

    cmd = [
        NODE_BIN,
        str(INSTAGRAM_ENGINE_SCRIPT),
        "--target", clean_target,
        "--count", str(count),
        "--type", target_type,
        "--output", str(out_file)
    ]
    if session:
        cmd.extend(["--session", session])
    if proxy:
        cmd.extend(["--proxy", proxy])
    if comments:
        cmd.append("--comments")

    add_log("OASIS Instagram Engine", f"Launching Flash Recon on target: @{clean_target} (Type: {target_type.upper()}, Items: {count}, Comments: {comments})", "info")
    add_recon_notification(
        tool="OASIS Instagram Intelligence Engine",
        status="PROCESSING",
        title="OASIS Instagram Recon Initiated",
        details=f"Harvesting public profile, metrics, and media grid for: @{clean_target}",
        target=clean_target,
        action_url="/services/social-media-intelligence"
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(INSTAGRAM_ENGINE_DIR)
        )

        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue
            add_log("OASIS Instagram Engine", line_str, "info")
            if "[OASIS]" in line_str or "[OASIS:SUCCESS]" in line_str:
                task["progress_msg"] = line_str.replace("[OASIS:SUCCESS]", "").replace("[OASIS]", "").strip()

        proc.stdout.close()
        return_code = proc.wait()

        if return_code != 0:
            task["status"] = "ERROR"
            task["error"] = "OASIS Instagram engine exited with an error. Check terminal telemetry."
            task["progress_msg"] = "Scraping failed."
            add_log("OASIS Instagram Engine", f"Process exited with code {return_code}", "error")
            update_tool_notification("OASIS Instagram Intelligence Engine", clean_target, "ERROR", details=f"Failed scraping @{clean_target}")
            return

        if out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                dossier = json.load(f)

            _save_instagram_dossier_files(clean_target, dossier)

            if download_zip:
                generate_instagram_media_zip(clean_target, dossier)

            task["status"] = "COMPLETED"
            task["duration"] = round(time.time() - task["start_time"], 1)
            task["profile"] = dossier.get("profile", {})
            task["posts"] = dossier.get("posts", [])
            task["stats"] = dossier.get("stats", {})
            task["progress_msg"] = f"Extraction completed. {len(task['posts'])} media artifacts harvested ({task['stats'].get('total_comments', 0)} comments)."

            _IG_CACHED_RESULTS[clean_target] = dossier

            add_log("OASIS Instagram Engine", f"OASIS Dossier ready for @{clean_target}: {len(task['posts'])} posts and {task['stats'].get('total_comments', 0)} comments extracted.", "success")
            update_tool_notification(
                "OASIS Instagram Intelligence Engine",
                clean_target,
                "FINISHED",
                title="OASIS Instagram Recon Completed",
                details=f"Extracted profile, {len(task['posts'])} posts, and {task['stats'].get('total_comments', 0)} comments for @{clean_target}",
                metrics=f"{len(task['posts'])} Media Items • Followers: {task['profile'].get('followers_str', 'N/A')}"
            )
        else:
            task["status"] = "ERROR"
            task["error"] = "Output file was not generated by engine."
            task["progress_msg"] = "Output file missing."
            update_tool_notification("OASIS Instagram Intelligence Engine", clean_target, "ERROR", details=f"Output missing for @{clean_target}")

    except Exception as e:
        task["status"] = "ERROR"
        task["error"] = str(e)
        task["progress_msg"] = f"Error: {e}"
        add_log("OASIS Instagram Engine", f"Exception during execution: {e}", "error")
        update_tool_notification("OASIS Instagram Intelligence Engine", clean_target, "ERROR", details=f"Exception for @{clean_target}: {e}")

def execute_instagram_task(
    target: str,
    mode: str = "flash",
    count: int = 8,
    target_type: str = "user",
    comments: bool = False,
    session: str = "",
    proxy: str = "",
    download_zip: bool = False,
    force: bool = False
) -> Dict[str, Any]:
    """Dispatches either Flash Mode (local OASIS engine) or Pro Mode (native cluster redirect)."""
    clean_target = _sanitize_ig_key(target)

    if mode.lower() == "pro":
        return {
            "mode": "pro",
            "redirect_url": NATIVE_SCRAPER_ENDPOINTS["instagram"]["url"],
            "target": clean_target,
            "status": "REDIRECT",
            "message": "Redirecting to OASIS high-capacity native scraper cluster."
        }

    # Flash Mode
    if not force:
        cached_file = REPORTS_DIR / f"instagram_{clean_target}.json"
        if cached_file.exists():
            try:
                with open(cached_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                return {
                    "mode": "flash",
                    "status": "COMPLETED",
                    "cached": True,
                    "target": clean_target,
                    "duration": 0.1,
                    "profile": cached_data.get("profile", {}),
                    "posts": cached_data.get("posts", []),
                    "stats": cached_data.get("stats", {}),
                    "progress_msg": "Loaded cached OASIS Instagram dossier from internal vault."
                }
            except Exception:
                pass

    with _IG_LOCK:
        if clean_target in _IG_TASKS and _IG_TASKS[clean_target].get("status") == "RUNNING":
            t = _IG_TASKS[clean_target]
            return {
                "mode": "flash",
                "status": "RUNNING",
                "target": clean_target,
                "elapsed": round(time.time() - t["start_time"], 1),
                "progress_msg": t.get("progress_msg", "Scraping in progress..."),
                "profile": {},
                "posts": []
            }

        task_record = {
            "mode": "flash",
            "target": clean_target,
            "status": "RUNNING",
            "start_time": time.time(),
            "duration": 0,
            "progress_msg": "Initializing OASIS Chromium Headless Engine...",
            "profile": {},
            "posts": [],
            "stats": {},
            "error": None
        }
        _IG_TASKS[clean_target] = task_record

        worker = threading.Thread(
            target=_run_instagram_flash_worker,
            args=(clean_target, count, session, target_type, comments, proxy, download_zip),
            daemon=True
        )
        worker.start()

        return {
            "mode": "flash",
            "status": "RUNNING",
            "target": clean_target,
            "elapsed": 0,
            "progress_msg": "OASIS Engine task dispatched to background worker."
        }

def get_instagram_status(target: str) -> Dict[str, Any]:
    """Retrieves live execution status or cached dossier for an Instagram target."""
    clean_target = _sanitize_ig_key(target)
    if clean_target in _IG_TASKS:
        t = _IG_TASKS[clean_target]
        elapsed = round(time.time() - t["start_time"], 1) if t["status"] == "RUNNING" else t.get("duration", 0)
        return {
            "target": clean_target,
            "mode": "flash",
            "status": t["status"],
            "elapsed": elapsed,
            "progress_msg": t.get("progress_msg", ""),
            "profile": t.get("profile", {}),
            "posts": t.get("posts", []),
            "stats": t.get("stats", {}),
            "error": t.get("error")
        }

    cached_file = REPORTS_DIR / f"instagram_{clean_target}.json"
    if cached_file.exists():
        try:
            with open(cached_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "target": clean_target,
                "mode": "flash",
                "status": "COMPLETED",
                "cached": True,
                "elapsed": 0,
                "progress_msg": "Retrieved from internal OASIS dossier vault.",
                "profile": data.get("profile", {}),
                "posts": data.get("posts", []),
                "stats": data.get("stats", {}),
                "error": None
            }
        except Exception:
            pass

    return {
        "target": clean_target,
        "mode": "flash",
        "status": "IDLE",
        "elapsed": 0,
        "progress_msg": "Ready to scan.",
        "profile": {},
        "posts": [],
        "stats": {},
        "error": None
    }

def ensure_instagram_report_file(target: str, fmt: str = "json") -> Optional[Path]:
    """Returns path to cached OASIS Instagram report format (JSON, MD, CSV, ZIP)."""
    clean_target = _sanitize_ig_key(target)
    fmt = fmt.lower().strip()
    if fmt == "csv":
        p = REPORTS_DIR / f"instagram_{clean_target}.csv"
        if p.exists(): return p
    elif fmt == "md":
        p = REPORTS_DIR / f"instagram_{clean_target}.md"
        if p.exists(): return p
    elif fmt == "zip":
        p = REPORTS_DIR / f"instagram_{clean_target}_media.zip"
        if p.exists(): return p
        cached_file = REPORTS_DIR / f"instagram_{clean_target}.json"
        if cached_file.exists():
            try:
                with open(cached_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return generate_instagram_media_zip(clean_target, data)
            except Exception:
                pass
    else:
        p = REPORTS_DIR / f"instagram_{clean_target}.json"
        if p.exists(): return p
    return None


# -----------------------------------------------------------------------------
# OASIS X / Twitter Intelligence Engine (Flash Mode / Pro Mode)
# -----------------------------------------------------------------------------
_TW_TASKS: Dict[str, Dict[str, Any]] = {}
_TW_CACHED_RESULTS: Dict[str, Dict[str, Any]] = {}
_TW_LOCK = threading.Lock()

def _sanitize_tw_key(target: str) -> str:
    cleaned = sanitize_x_target(target)
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned)

def _save_twitter_dossier_files(clean_target: str, data: Dict[str, Any]):
    """Persists JSON, Markdown, and CSV dossiers for Twitter/X recon with full OASIS branding."""
    # 1. JSON Report
    json_path = REPORTS_DIR / f"twitter_{clean_target}.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        add_log("OASIS Twitter Engine", f"Failed saving JSON report: {e}", "warning")

    profile = data.get("profile", {})
    tweets = data.get("tweets", [])
    stats = data.get("stats", {})

    # 2. Markdown Incident Dossier
    try:
        md_path = REPORTS_DIR / f"twitter_{clean_target}.md"
        md_lines = [
            "# OASIS Intelligence Dossier: X / Twitter Reconnaissance",
            "",
            "> **CONFIDENTIAL INVESTIGATION PRODUCT**  ",
            "> Generated by OASIS Strategic OSINT Suite — X/Twitter Flash Intelligence Engine  ",
            f"> **Target Identifier:** `@{profile.get('username', clean_target)}` | **Investigation Timestamp:** {data.get('timestamp')}",
            "",
            "---",
            "",
            "## 1. Subject Profile & Account Identity",
            "",
            f"- **Username / Handle:** `@{profile.get('username', clean_target)}`",
            f"- **Display Name:** {profile.get('displayname', 'N/A')}",
            f"- **Verification:** {'[VERIFIED] Verified / Blue Badge' if profile.get('verified') else 'Unverified User'}",
            f"- **Audience Reach (Followers):** {profile.get('followers_count', 0):,} followers",
            f"- **Following (Friends):** {profile.get('following_count', 0):,} following",
            f"- **Total Posts (Statuses):** {profile.get('statuses_count', 0):,} tweets",
            f"- **Account Created:** {profile.get('created', 'N/A')}",
            f"- **Location:** {profile.get('location', 'Unspecified')}",
            f"- **Biography / Bio:** {profile.get('bio') or 'No bio provided'}",
            f"- **Profile URL:** [{profile.get('url', f'https://x.com/{clean_target}')}]({profile.get('url', f'https://x.com/{clean_target}')})",
            "",
            "---",
            "",
            f"## 2. Extracted Timeline Tweets & Engagements ({len(tweets)})",
            "",
            "| # | Date (UTC) | Tweet Text | Engagement (Likes / RT / Replies) | Client / Source | Link |",
            "|---|---|---|---|---|---|"
        ]

        if tweets:
            for idx, tw in enumerate(tweets, 1):
                dt = tw.get("date", "N/A")
                txt = tw.get("text", "").replace("\n", " ").replace("|", "\\|")
                if len(txt) > 120:
                    txt = txt[:117] + "..."
                likes = tw.get("like_count", 0)
                rts = tw.get("retweet_count", 0)
                replies = tw.get("reply_count", 0)
                src = tw.get("source", "Web")
                url = tw.get("url", f"https://x.com/i/status/{tw.get('id', '')}")
                md_lines.append(f"| {idx} | {dt} | {txt} | Likes: {likes} • RTs: {rts} • Replies: {replies} | `{src}` | [View ↗]({url}) |")
        else:
            md_lines.append("| - | - | *No tweets extracted* | - | - | - |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Investigation Integrity & Evidence Details",
            "",
            "- **Engine:** OASIS X / Twitter Intelligence Engine (Flash Mode)",
            "- **Target Ecosystem:** X / Twitter GraphQL Endpoints",
            "- **Harvested Artifacts:** Profile metadata, tweet engagement metrics, client applications, media links",
            ""
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
    except Exception as e:
        add_log("OASIS Twitter Engine", f"Failed saving Markdown report: {e}", "warning")

    # 3. CSV Report
    try:
        import csv
        csv_path = REPORTS_DIR / f"twitter_{clean_target}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "OASIS_Index", "Tweet_ID", "Author_Username", "Date_UTC", "Content",
                "Likes", "Retweets", "Replies", "Quotes", "Views", "Source_Client", "URL"
            ])
            for idx, tw in enumerate(tweets, 1):
                writer.writerow([
                    idx,
                    tw.get("id", ""),
                    tw.get("user", {}).get("username", clean_target),
                    tw.get("date", ""),
                    tw.get("text", ""),
                    tw.get("like_count", 0),
                    tw.get("retweet_count", 0),
                    tw.get("reply_count", 0),
                    tw.get("quote_count", 0),
                    tw.get("view_count", 0),
                    tw.get("source", ""),
                    tw.get("url", "")
                ])
    except Exception as e:
        add_log("OASIS Twitter Engine", f"Failed saving CSV report: {e}", "warning")

def _background_twitter_worker(
    target: str,
    clean_target: str,
    count: int,
    target_type: str,
    session: str,
    proxy: str,
    min_likes: int = 0,
    min_retweets: int = 0,
    since_date: str = "",
    until_date: str = "",
    lang: str = "",
    media_only: bool = False,
    links_only: bool = False
):
    """Background worker thread executing native X/Twitter GraphQL queries with live status."""
    task = _TW_TASKS[clean_target]

    add_log("OASIS Twitter Engine", f"Launching Flash Twitter Recon on: @{clean_target} (Type: {target_type.upper()}, Items: {count})", "info")
    add_recon_notification(
        tool="OASIS Twitter Intelligence Engine",
        status="PROCESSING",
        title="OASIS Twitter Recon Initiated",
        details=f"Querying X/Twitter GraphQL for: @{clean_target}",
        target=clean_target,
        action_url="/services/social-media-intelligence"
    )

    try:
        task["progress_msg"] = f"Connecting to X/Twitter GraphQL for @{clean_target}..."
        result = scrape_twitter(
            target=clean_target,
            count=count,
            target_type=target_type,
            session_cookie=session,
            proxy=proxy,
            min_likes=min_likes,
            min_retweets=min_retweets,
            since_date=since_date,
            until_date=until_date,
            lang=lang,
            media_only=media_only,
            links_only=links_only
        )

        _save_twitter_dossier_files(clean_target, result)

        with _TW_LOCK:
            task["status"] = "COMPLETED"
            task["duration"] = result.get("duration", round(time.time() - task["start_time"], 1))
            task["profile"] = result.get("profile", {})
            task["tweets"] = result.get("tweets", [])
            task["stats"] = result.get("stats", {})
            task["progress_msg"] = f"Extraction complete: profile and {len(task['tweets'])} tweets harvested in {task['duration']}s."
            _TW_CACHED_RESULTS[clean_target] = result

        add_log("OASIS Twitter Engine", f"OASIS Twitter Dossier ready for @{clean_target}: {len(task['tweets'])} tweets extracted in {task['duration']}s.", "success")
        update_tool_notification(
            "OASIS Twitter Intelligence Engine",
            clean_target,
            "FINISHED",
            title="OASIS Twitter Recon Completed",
            details=f"Extracted profile and {len(task['tweets'])} tweets for @{clean_target}",
            metrics=f"{len(task['tweets'])} Tweets • Followers: {task['profile'].get('followers_count', 0):,}"
        )

    except Exception as e:
        err_msg = str(e)
        with _TW_LOCK:
            task["status"] = "ERROR"
            task["error"] = err_msg
            task["progress_msg"] = f"Error: {err_msg}"
        add_log("OASIS Twitter Engine", f"Execution error for @{clean_target}: {err_msg}", "error")
        update_tool_notification("OASIS Twitter Intelligence Engine", clean_target, "ERROR", details=f"Twitter engine error: {err_msg}")

def execute_twitter_task(
    target: str,
    mode: str = "flash",
    count: int = 10,
    target_type: str = "user",
    session: str = "",
    proxy: str = "",
    force: bool = False,
    min_likes: int = 0,
    min_retweets: int = 0,
    since_date: str = "",
    until_date: str = "",
    lang: str = "",
    media_only: bool = False,
    links_only: bool = False
) -> Dict[str, Any]:
    """Dispatches either Twitter Flash Mode (native GraphQL engine) or Pro Mode (cluster redirect)."""
    clean_target = _sanitize_tw_key(target)

    if mode.lower() == "pro":
        return {
            "mode": "pro",
            "redirect_url": NATIVE_SCRAPER_ENDPOINTS["x"]["url"],
            "target": clean_target,
            "status": "REDIRECT",
            "message": "Redirecting to OASIS high-capacity X / Twitter native scraper cluster."
        }

    # Flash Mode (native GraphQL engine)
    if not force:
        cached_file = REPORTS_DIR / f"twitter_{clean_target}.json"
        if cached_file.exists():
            try:
                with open(cached_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                return {
                    "mode": "flash",
                    "status": "COMPLETED",
                    "cached": True,
                    "target": clean_target,
                    "elapsed": 0.1,
                    "duration": cached_data.get("duration", 0.1),
                    "profile": cached_data.get("profile", {}),
                    "tweets": cached_data.get("tweets", []),
                    "stats": cached_data.get("stats", {}),
                    "progress_msg": f"Retrieved from internal OASIS dossier vault ({len(cached_data.get('tweets', []))} tweets)."
                }
            except Exception:
                pass

    with _TW_LOCK:
        if clean_target in _TW_TASKS and _TW_TASKS[clean_target].get("status") == "RUNNING":
            t = _TW_TASKS[clean_target]
            return {
                "mode": "flash",
                "status": "RUNNING",
                "target": clean_target,
                "elapsed": round(time.time() - t["start_time"], 1),
                "progress_msg": t.get("progress_msg", "Reconnaissance in progress..."),
                "profile": t.get("profile", {}),
                "tweets": t.get("tweets", []),
                "stats": t.get("stats", {})
            }

        task_record = {
            "target": clean_target,
            "mode": "flash",
            "status": "RUNNING",
            "start_time": time.time(),
            "duration": 0,
            "progress_msg": f"Dispatching OASIS Twitter Engine for @{clean_target}...",
            "profile": {},
            "tweets": [],
            "stats": {},
            "error": None
        }
        _TW_TASKS[clean_target] = task_record

    worker = threading.Thread(
        target=_background_twitter_worker,
        args=(target, clean_target, count, target_type, session, proxy, min_likes, min_retweets, since_date, until_date, lang, media_only, links_only),
        daemon=True
    )
    worker.start()

    return {
        "mode": "flash",
        "status": "RUNNING",
        "target": clean_target,
        "elapsed": 0,
        "progress_msg": f"OASIS Twitter Engine dispatched to background worker for @{clean_target}."
    }

def get_twitter_status(target: str) -> Dict[str, Any]:
    """Retrieves live execution status or cached dossier for a Twitter target."""
    clean_target = _sanitize_tw_key(target)
    if clean_target in _TW_TASKS:
        t = _TW_TASKS[clean_target]
        elapsed = round(time.time() - t["start_time"], 1) if t["status"] == "RUNNING" else t.get("duration", 0)
        return {
            "target": clean_target,
            "mode": "flash",
            "status": t["status"],
            "elapsed": elapsed,
            "progress_msg": t.get("progress_msg", ""),
            "profile": t.get("profile", {}),
            "tweets": t.get("tweets", []),
            "stats": t.get("stats", {}),
            "error": t.get("error")
        }

    cached_file = REPORTS_DIR / f"twitter_{clean_target}.json"
    if cached_file.exists():
        try:
            with open(cached_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "target": clean_target,
                "mode": "flash",
                "status": "COMPLETED",
                "cached": True,
                "elapsed": 0,
                "progress_msg": "Retrieved from internal OASIS dossier vault.",
                "profile": data.get("profile", {}),
                "tweets": data.get("tweets", []),
                "stats": data.get("stats", {}),
                "error": None
            }
        except Exception:
            pass

    return {
        "target": clean_target,
        "mode": "flash",
        "status": "IDLE",
        "elapsed": 0,
        "progress_msg": "Ready to scan.",
        "profile": {},
        "tweets": [],
        "stats": {},
        "error": None
    }

def ensure_twitter_report_file(target: str, fmt: str = "json") -> Optional[Path]:
    """Returns path to cached OASIS Twitter report format (JSON, MD, CSV)."""
    clean_target = _sanitize_tw_key(target)
    fmt = fmt.lower().strip()
    if fmt == "csv":
        p = REPORTS_DIR / f"twitter_{clean_target}.csv"
        if p.exists(): return p
    elif fmt == "md":
        p = REPORTS_DIR / f"twitter_{clean_target}.md"
        if p.exists(): return p
    else:
        p = REPORTS_DIR / f"twitter_{clean_target}.json"
        if p.exists(): return p
    return None

# -----------------------------------------------------------------------------
# Dedicated OASIS LinkedIn Intelligence Engine (Flash & Pro Modes)
# -----------------------------------------------------------------------------
_LI_TASKS: Dict[str, Dict[str, Any]] = {}
_LI_CACHED_RESULTS: Dict[str, Dict[str, Any]] = {}
_LI_LOCK = threading.Lock()

def _sanitize_li_key(company: str) -> str:
    cleaned = clean_company_name(company)
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned).lower()

def _save_linkedin_dossier_files(clean_company: str, data: Dict[str, Any]):
    """Persists JSON, Markdown, and CSV dossiers for LinkedIn workforce reconnaissance."""
    # 1. JSON Report
    json_path = REPORTS_DIR / f"linkedin_{clean_company}.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        add_log("OASIS LinkedIn Engine", f"Failed saving JSON report: {e}", "warning")

    personnel = data.get("personnel", [])

    # 2. Markdown Incident Dossier
    try:
        md_path = REPORTS_DIR / f"linkedin_{clean_company}.md"
        md_lines = [
            "# OASIS Intelligence Dossier: LinkedIn Corporate Workforce Reconnaissance",
            "",
            "> **CONFIDENTIAL INVESTIGATION PRODUCT**  ",
            "> Generated by OASIS Strategic OSINT Suite — LinkedIn Flash Workforce Engine  ",
            f"> **Target Corporation:** `{data.get('company', clean_company)}` | **Investigation Timestamp:** {data.get('timestamp')}",
            "",
            "---",
            "",
            "## 1. Executive Summary & Scope",
            "",
            f"- **Target Corporation:** `{data.get('company', clean_company)}`",
            f"- **Identified Corporate Domain:** `{data.get('domain', 'N/A')}`",
            f"- **Total Discovered Personnel:** {len(personnel)} verified profiles",
            f"- **Email Inference Formula:** `{data.get('email_pattern', 'N/A')}`",
            f"- **Department / Role Filter:** `{data.get('title_filter') or 'All Roles'}`",
            f"- **Search Index Providers:** {', '.join(data.get('engines_queried', []))}",
            "",
            "---",
            "",
            f"## 2. Identified Corporate Personnel ({len(personnel)})",
            "",
            "| # | Name | Professional Role / Title | Inferred Email | LinkedIn Profile |",
            "|---|---|---|---|---|"
        ]

        if personnel:
            for idx, p in enumerate(personnel, 1):
                name = p.get("name", "Unknown Individual")
                title = p.get("title", "N/A").replace("|", "\\|")
                email = p.get("inferred_email", "N/A")
                url = p.get("profile_url", "#")
                md_lines.append(f"| {idx} | **{name}** | {title} | `{email}` | [View Profile ↗]({url}) |")
        else:
            md_lines.append("| - | *No corporate personnel discovered* | - | - | - |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 3. Investigation Integrity & Evidence Details",
            "",
            "- **Engine:** OASIS LinkedIn Workforce Engine (Flash Mode)",
            "- **Target Ecosystem:** LinkedIn Public Indexation & Corporate Identity Graph",
            "- **Discovery Mode:** Zero-credential non-intrusive index harvesting",
            ""
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
    except Exception as e:
        add_log("OASIS LinkedIn Engine", f"Failed saving Markdown report: {e}", "warning")

    # 3. CSV Report
    try:
        import csv
        csv_path = REPORTS_DIR / f"linkedin_{clean_company}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "OASIS_Index", "Target_Company", "Person_Name", "Job_Title",
                "Inferred_Email", "LinkedIn_Profile_URL", "Search_Engine"
            ])
            for idx, p in enumerate(personnel, 1):
                writer.writerow([
                    idx,
                    data.get("company", clean_company),
                    p.get("name", ""),
                    p.get("title", ""),
                    p.get("inferred_email", ""),
                    p.get("profile_url", ""),
                    p.get("source_engine", "")
                ])
    except Exception as e:
        add_log("OASIS LinkedIn Engine", f"Failed saving CSV report: {e}", "warning")

def _background_linkedin_worker(
    company: str,
    clean_company: str,
    title_filter: str,
    engine: str,
    domain: str,
    pattern: str,
    timeout: float,
    jitter: float,
    max_results: int,
    proxy: str
):
    """Background worker thread executing LinkedIn workforce scraping with live status."""
    task = _LI_TASKS[clean_company]

    add_log("OASIS LinkedIn Engine", f"Launching Flash LinkedIn Workforce Recon on: {clean_company} (Filter: {title_filter or 'ALL'})", "info")
    add_recon_notification(
        tool="OASIS LinkedIn Intelligence Engine",
        status="PROCESSING",
        title="OASIS LinkedIn Recon Initiated",
        details=f"Harvesting corporate personnel directory for: {clean_company}",
        target=clean_company,
        action_url="/services/social-media-intelligence"
    )

    try:
        task["progress_msg"] = f"Harvesting public LinkedIn personnel index for {clean_company}..."
        result = scrape_linkedin_workforce(
            company_name=clean_company,
            title_filter=title_filter,
            engine=engine,
            domain=domain,
            pattern=pattern,
            timeout=timeout,
            jitter=jitter,
            max_results=max_results,
            proxy=proxy
        )

        _save_linkedin_dossier_files(clean_company, result)

        with _LI_LOCK:
            task["status"] = "COMPLETED"
            task["duration"] = result.get("duration", round(time.time() - task["start_time"], 1))
            task["company"] = result.get("company", clean_company)
            task["domain"] = result.get("domain", "")
            task["personnel"] = result.get("personnel", [])
            task["total_discovered"] = result.get("total_discovered", len(task["personnel"]))
            task["progress_msg"] = f"Corporate workforce harvested: {len(task['personnel'])} profiles identified in {task['duration']}s."
            _LI_CACHED_RESULTS[clean_company] = result

        add_log("OASIS LinkedIn Engine", f"LinkedIn Workforce Dossier ready for {clean_company}: {len(task['personnel'])} profiles harvested in {task['duration']}s.", "success")
        update_tool_notification(
            "OASIS LinkedIn Intelligence Engine",
            clean_company,
            "FINISHED",
            title="OASIS LinkedIn Recon Completed",
            details=f"Extracted {len(task['personnel'])} corporate personnel for {clean_company}",
            metrics=f"{len(task['personnel'])} Personnel • Domain: {task['domain']}"
        )

    except Exception as e:
        err_msg = str(e)
        with _LI_LOCK:
            task["status"] = "ERROR"
            task["error"] = err_msg
            task["progress_msg"] = f"Error: {err_msg}"
        add_log("OASIS LinkedIn Engine", f"Execution error for {clean_company}: {err_msg}", "error")
        update_tool_notification("OASIS LinkedIn Intelligence Engine", clean_company, "ERROR", details=f"LinkedIn engine error: {err_msg}")

def execute_linkedin_task(
    company: str,
    mode: str = "flash",
    title_filter: str = "",
    engine: str = "yahoo,bing,google",
    domain: str = "",
    pattern: str = "{first}.{last}@{domain}",
    timeout: float = 15.0,
    jitter: float = 0.5,
    max_results: int = 50,
    proxy: str = "",
    force: bool = False
) -> Dict[str, Any]:
    """Dispatches either LinkedIn Flash Mode (public search indexation) or Pro Mode (enterprise cluster)."""
    clean_company = _sanitize_li_key(company)

    if mode.lower() == "pro":
        return {
            "mode": "pro",
            "redirect_url": NATIVE_SCRAPER_ENDPOINTS.get("linkedin", {}).get("url", "https://www.linkedin.com/"),
            "target": clean_company,
            "status": "REDIRECT",
            "message": "Redirecting to OASIS enterprise LinkedIn crawler cluster."
        }

    # Flash Mode
    if not force:
        cached_file = REPORTS_DIR / f"linkedin_{clean_company}.json"
        if cached_file.exists():
            try:
                with open(cached_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                return {
                    "mode": "flash",
                    "status": "COMPLETED",
                    "cached": True,
                    "company": cached_data.get("company", clean_company),
                    "domain": cached_data.get("domain", ""),
                    "elapsed": 0.1,
                    "duration": cached_data.get("duration", 0.1),
                    "personnel": cached_data.get("personnel", []),
                    "total_discovered": cached_data.get("total_discovered", len(cached_data.get("personnel", []))),
                    "progress_msg": f"Retrieved from internal OASIS dossier vault ({len(cached_data.get('personnel', []))} personnel)."
                }
            except Exception:
                pass

    with _LI_LOCK:
        if clean_company in _LI_TASKS and _LI_TASKS[clean_company].get("status") == "RUNNING":
            t = _LI_TASKS[clean_company]
            return {
                "mode": "flash",
                "status": "RUNNING",
                "company": clean_company,
                "elapsed": round(time.time() - t["start_time"], 1),
                "progress_msg": t.get("progress_msg", "Workforce discovery in progress..."),
                "personnel": t.get("personnel", []),
                "total_discovered": len(t.get("personnel", []))
            }

        task_record = {
            "company": clean_company,
            "mode": "flash",
            "status": "RUNNING",
            "start_time": time.time(),
            "duration": 0,
            "progress_msg": f"Dispatching OASIS LinkedIn Workforce Engine for {clean_company}...",
            "personnel": [],
            "total_discovered": 0,
            "error": None
        }
        _LI_TASKS[clean_company] = task_record

    worker = threading.Thread(
        target=_background_linkedin_worker,
        args=(company, clean_company, title_filter, engine, domain, pattern, timeout, jitter, max_results, proxy),
        daemon=True
    )
    worker.start()

    return {
        "mode": "flash",
        "status": "RUNNING",
        "company": clean_company,
        "elapsed": 0,
        "progress_msg": f"OASIS LinkedIn Workforce Engine dispatched to background worker for {clean_company}."
    }

def get_linkedin_status(company: str) -> Dict[str, Any]:
    """Retrieves live execution status or cached dossier for a LinkedIn corporate target."""
    clean_company = _sanitize_li_key(company)
    if clean_company in _LI_TASKS:
        t = _LI_TASKS[clean_company]
        elapsed = round(time.time() - t["start_time"], 1) if t["status"] == "RUNNING" else t.get("duration", 0)
        return {
            "company": clean_company,
            "mode": "flash",
            "status": t["status"],
            "elapsed": elapsed,
            "progress_msg": t.get("progress_msg", ""),
            "domain": t.get("domain", ""),
            "personnel": t.get("personnel", []),
            "total_discovered": t.get("total_discovered", len(t.get("personnel", []))),
            "error": t.get("error")
        }

    cached_file = REPORTS_DIR / f"linkedin_{clean_company}.json"
    if cached_file.exists():
        try:
            with open(cached_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "company": clean_company,
                "mode": "flash",
                "status": "COMPLETED",
                "cached": True,
                "elapsed": 0,
                "progress_msg": "Retrieved from internal OASIS dossier vault.",
                "domain": data.get("domain", ""),
                "personnel": data.get("personnel", []),
                "total_discovered": data.get("total_discovered", len(data.get("personnel", []))),
                "error": None
            }
        except Exception:
            pass

    return {
        "company": clean_company,
        "mode": "flash",
        "status": "IDLE",
        "elapsed": 0,
        "progress_msg": "Ready to scan.",
        "domain": "",
        "personnel": [],
        "total_discovered": 0,
        "error": None
    }

def ensure_linkedin_report_file(company: str, fmt: str = "json") -> Optional[Path]:
    """Returns path to cached OASIS LinkedIn report format (JSON, MD, CSV)."""
    clean_company = _sanitize_li_key(company)
    fmt = fmt.lower().strip()
    if fmt == "csv":
        p = REPORTS_DIR / f"linkedin_{clean_company}.csv"
        if p.exists(): return p
    elif fmt == "md":
        p = REPORTS_DIR / f"linkedin_{clean_company}.md"
        if p.exists(): return p
    else:
        p = REPORTS_DIR / f"linkedin_{clean_company}.json"
        if p.exists(): return p
    return None


