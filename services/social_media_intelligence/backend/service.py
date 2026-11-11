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

# Reports and Output Storage Directory
REPORTS_DIR = BASE_DIR / "services" / "social_media_intelligence" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Engine Python interpreter (use maigret venv which has rich social registry)
MAIGRET_DIR = (BASE_DIR.parent / "maigret").resolve()
ENGINE_PYTHON = str(MAIGRET_DIR / ".venv" / "bin" / "python")
if not os.path.exists(ENGINE_PYTHON):
    ENGINE_PYTHON = sys.executable

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
    """Loads previous social media findings from JSON report."""
    clean_target = target.strip()
    json_path = REPORTS_DIR / f"report_{clean_target}_simple.json"
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
