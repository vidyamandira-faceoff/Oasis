import os
import sys
import time
import json
import ast
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.config import BASE_DIR
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

# Reports and Output Storage Directory
REPORTS_DIR = BASE_DIR / "services" / "recon_username" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Locate the Python environment equipped with the reconnaissance engine
def _get_engine_python() -> str:
    # Priority 1: sibling workspace directory
    cand1 = BASE_DIR.parent / "maigret" / ".venv" / "bin" / "python"
    if cand1.exists():
        return str(cand1)
    
    # Priority 2: local oasis venv
    cand2 = BASE_DIR / ".venv" / "bin" / "python"
    if cand2.exists():
        return str(cand2)
        
    # Priority 3: current running python
    return sys.executable

ENGINE_PYTHON = _get_engine_python()

# In-memory Task State and Cache
_TASKS: Dict[str, Dict[str, Any]] = {}
_CACHED_RESULTS: Dict[str, Dict[str, Any]] = {}
_SUBPROCESSES: Dict[str, subprocess.Popen] = {}
_RUNNING_LOCK = threading.Lock()

def sanitize_text(text: str) -> str:
    """Removes any internal tool engine brand names from logs and text."""
    if not text:
        return ""
    # Case-insensitive replacement of engine brand
    import re
    cleaned = re.sub(r'(?i)maigret', 'Username Reconnaissance Engine', text)
    return cleaned

def parse_profile_links(raw_links: Any) -> List[str]:
    """Safely extracts outbound URLs from bio/links data."""
    if isinstance(raw_links, list):
        return [str(l).strip() for l in raw_links if l]
    if isinstance(raw_links, str):
        raw_str = raw_links.strip()
        if raw_str.startswith("[") and raw_str.endswith("]"):
            try:
                parsed = ast.literal_eval(raw_str)
                if isinstance(parsed, list):
                    return [str(l).strip() for l in parsed if l]
            except Exception:
                pass
        if raw_str.startswith("http://") or raw_str.startswith("https://"):
            return [raw_str]
    return []

def load_cached_report_from_disk(target: str) -> Optional[Dict[str, Any]]:
    """Attempts to load previously generated JSON report from disk."""
    json_path = REPORTS_DIR / f"report_{target}_simple.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return _normalize_report_data(target, raw_data)
    except Exception as e:
        add_log("Username Intelligence", f"Error reading stored report for {target}: {e}", "warning")
        return None

def _normalize_report_data(target: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms raw engine output into clean OASIS findings schema."""
    findings = []
    unique_tags = set()
    enriched_count = 0

    for site_name, item in raw_data.items():
        if not isinstance(item, dict):
            continue
            
        status_obj = item.get("status") or {}
        site_obj = item.get("site") or {}
        ids = status_obj.get("ids") or item.get("ids") or {}

        profile_url = (
            item.get("url_user") or 
            status_obj.get("url") or 
            site_obj.get("url", "").replace("{username}", target)
        )
        
        tags = status_obj.get("tags") or site_obj.get("tags") or []
        for t in tags:
            if t:
                unique_tags.add(str(t).lower())

        fullname = ids.get("fullname") or ids.get("name") or ""
        bio = ids.get("bio") or ids.get("description") or ""
        avatar = ids.get("image") or ids.get("avatar") or ""
        location = ids.get("location") or ids.get("country") or ""
        followers = ids.get("follower_count") or ids.get("followers") or ""
        following = ids.get("following_count") or ""
        created_at = ids.get("created_at") or ""
        
        outbound_links = parse_profile_links(ids.get("links") or item.get("ids_links"))

        is_enriched = bool(fullname or bio or avatar or location or outbound_links)
        if is_enriched:
            enriched_count += 1

        alexa_rank = site_obj.get("alexaRank") or item.get("rank")
        try:
            alexa_rank = int(alexa_rank) if alexa_rank is not None else 99999
        except (ValueError, TypeError):
            alexa_rank = 99999

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
            "links": outbound_links,
            "raw_metadata": {k: v for k, v in ids.items() if not k.startswith("_")}
        })

    # Sort findings: enriched profiles and high-priority Alexa platforms first
    findings.sort(key=lambda x: (
        0 if (x["bio"] or x["fullname"] or x["avatar"]) else 1,
        x["alexa_rank"]
    ))

    result_payload = {
        "target": target,
        "total_claimed": len(findings),
        "enriched_count": enriched_count,
        "tags": sorted(list(unique_tags)),
        "findings": findings,
        "files": {
            "json": str(REPORTS_DIR / f"report_{target}_simple.json"),
            "csv": str(REPORTS_DIR / f"report_{target}.csv"),
            "html": str(REPORTS_DIR / f"report_{target}_plain.html"),
            "txt": str(REPORTS_DIR / f"report_{target}.txt"),
        }
    }
    return result_payload

def _run_recon_worker(
    target: str,
    scope: str,
    category: str,
    timeout: int,
    id_type: str = "username",
    enrich: bool = False,
    with_domains: bool = False,
    recursive: bool = True,
    tor: bool = False
):
    """Background worker executing the reconnaissance engine."""
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
        "-H",
        "-M",
        "--no-color",
        "--no-progressbar",
        "--no-autoupdate",
    ]

    # Scope handling
    if scope == "quick":
        cmd.extend(["--top-sites", "100", "--timeout", str(max(3, timeout or 5))])
    elif scope == "deep":
        cmd.extend(["-a", "--timeout", str(max(6, timeout or 8))])
    else:  # standard (default)
        cmd.extend(["--top-sites", "500", "--timeout", str(max(5, timeout or 6))])

    # Category / Tag filter handling
    if category and category != "all":
        cmd.extend(["--tags", category])

    # Identifier type pivot (e.g. gaia_id, steam_id, vk_id)
    if id_type and id_type != "username":
        cmd.extend(["--id-type", id_type])

    # Advanced feature toggles
    if enrich:
        cmd.append("--enrich")
    if with_domains:
        cmd.append("--with-domains")
    if not recursive:
        cmd.append("--no-recursion")
    if tor:
        cmd.extend(["--tor-proxy", "socks5://127.0.0.1:9050"])

    cmd.extend(["-n", "40"])

    add_log("Username Intelligence", f"Launching reconnaissance engine for handle: {clean_target} (Scope: {scope}, ID-Type: {id_type})", "info")
    add_recon_notification(
        tool="Username Intelligence",
        status="PROCESSING",
        title="Username Reconnaissance Query Initiated",
        details=f"Querying global platform registries for target: {clean_target}",
        target=clean_target,
        action_url=f"/services/recon-username?target={clean_target}"
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
            
            # Detect starting count of sites
            if "Starting a search on top" in line_str:
                parts = line_str.split("top ")
                if len(parts) > 1:
                    try:
                        num = int(parts[1].split()[0])
                        task_info["total_sites"] = num
                    except Exception:
                        pass
                task_info["progress_msg"] = sanitize_text(line_str)

            # Detect claimed profiles live: e.g. "[+] GitHub: https://github.com/..."
            elif line_str.startswith("[+]") and ":" in line_str and not "Using sites" in line_str:
                content = line_str[3:].strip()
                tokens = content.split(":", 1)
                if len(tokens) == 2:
                    p_name = tokens[0].strip()
                    p_url = tokens[1].strip()
                    if p_url.startswith("http://") or p_url.startswith("https://"):
                        task_info["discovered_items"].append({"platform": p_name, "url": p_url})
                        task_info["discovered_count"] = len(task_info["discovered_items"])
                        task_info["progress_msg"] = f"Identified active profile on {p_name}"

        proc.wait()

        # Load and normalize final report
        normalized = load_cached_report_from_disk(clean_target)
        if not normalized:
            # Fallback if no simple JSON generated
            normalized = {
                "target": clean_target,
                "total_claimed": len(task_info["discovered_items"]),
                "enriched_count": 0,
                "tags": [],
                "findings": [
                    {
                        "platform": item["platform"],
                        "url": item["url"],
                        "status": "Claimed",
                        "alexa_rank": 99999,
                        "tags": [],
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
        task_info["progress_msg"] = f"Reconnaissance completed. {normalized['total_claimed']} profiles claimed."

        update_tool_notification(
            tool="Username Intelligence",
            target=clean_target,
            new_status="FINISHED",
            title="Username Reconnaissance Completed",
            details=f"Harvested {normalized['total_claimed']} verified accounts across {task_info.get('total_sites', 500)} platform registries.",
            metrics=f"{normalized['total_claimed']} Accounts • {normalized['enriched_count']} Dossiers Enriched"
        )
        add_log("Username Intelligence", f"Finished reconnaissance for {clean_target}: {normalized['total_claimed']} profiles found in {task_info['duration']}s.", "success")

        # Sanitize HTML report branding if generated
        html_file = REPORTS_DIR / f"report_{clean_target}_plain.html"
        if html_file.exists():
            try:
                html_text = html_file.read_text(encoding="utf-8")
                html_text = re.sub(r'(?i)maigret\s+username\s+search\s+report', 'OASIS Username Intelligence Dossier', html_text)
                html_text = re.sub(r'<small\s+class="text-muted">Generated\s+by\s+<a\s+href="[^"]*">Maigret</a>', '<small class="text-muted">Generated by <strong>OASIS Reconnaissance Platform</strong>', html_text)
                html_text = re.sub(r'(?i)maigret', 'OASIS Intelligence Engine', html_text)
                html_file.write_text(html_text, encoding="utf-8")
            except Exception:
                pass

        md_file = REPORTS_DIR / f"report_{clean_target}.md"
        if md_file.exists():
            try:
                md_text = md_file.read_text(encoding="utf-8")
                md_text = re.sub(r'(?i)maigret', 'OASIS Reconnaissance Engine', md_text)
                md_file.write_text(md_text, encoding="utf-8")
            except Exception:
                pass

    except Exception as e:
        task_info["status"] = "ERROR"
        task_info["error"] = sanitize_text(str(e))
        task_info["duration"] = round(time.time() - task_info["start_time"], 1)
        add_log("Username Intelligence", f"Error during reconnaissance execution: {e}", "error")
        update_tool_notification(
            tool="Username Intelligence",
            target=clean_target,
            new_status="FINISHED",
            title="Username Reconnaissance Error",
            details=sanitize_text(str(e))
        )

def _safe_task_dict(t: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures task dictionary is strictly JSON serializable with no internal locks/objects."""
    return {
        "target": t.get("target", ""),
        "status": t.get("status", "IDLE"),
        "cached": bool(t.get("cached", False)),
        "duration": t.get("duration", 0),
        "total_sites": t.get("total_sites", 500),
        "discovered_count": t.get("discovered_count", 0),
        "discovered_items": t.get("discovered_items", [])[-8:],
        "findings": t.get("findings", []),
        "stats": t.get("stats", {}),
        "progress_msg": t.get("progress_msg", ""),
        "error": t.get("error")
    }

def execute_recon_task(
    target: str,
    scope: str = "standard",
    category: str = "all",
    timeout: int = 6,
    force: bool = False,
    id_type: str = "username",
    enrich: bool = False,
    with_domains: bool = False,
    recursive: bool = True,
    tor: bool = False
) -> Dict[str, Any]:
    """Triggers or retrieves reconnaissance task for a target username."""
    clean_target = target.strip()
    if not clean_target:
        raise ValueError("Target handle cannot be empty.")

    # If force re-run requested, wipe previous cache and files
    if force:
        json_path = REPORTS_DIR / f"report_{clean_target}_simple.json"
        csv_path = REPORTS_DIR / f"report_{clean_target}.csv"
        txt_path = REPORTS_DIR / f"report_{clean_target}.txt"
        html_path = REPORTS_DIR / f"report_{clean_target}_plain.html"
        md_path = REPORTS_DIR / f"report_{clean_target}.md"
        for p in [json_path, csv_path, txt_path, html_path, md_path]:
            if p.exists():
                try: p.unlink()
                except Exception: pass
        _CACHED_RESULTS.pop(clean_target, None)
        _TASKS.pop(clean_target, None)
    else:
        # Check cache first if not forced
        cached = load_cached_report_from_disk(clean_target)
        if cached:
            _CACHED_RESULTS[clean_target] = cached
            return {
                "status": "COMPLETED",
                "cached": True,
                "target": clean_target,
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
                "progress_msg": f"Loaded {cached['total_claimed']} cached findings from local storage."
            }

    with _RUNNING_LOCK:
        # If task already running, return existing state safely
        if clean_target in _TASKS and _TASKS[clean_target].get("status") == "RUNNING":
            return _safe_task_dict(_TASKS[clean_target])

        task_record = {
            "target": clean_target,
            "status": "RUNNING",
            "cached": False,
            "start_time": time.time(),
            "duration": 0,
            "total_sites": 100 if scope == "quick" else (3000 if scope == "deep" else 500),
            "discovered_count": 0,
            "discovered_items": [],
            "findings": [],
            "progress_msg": "Initializing reconnaissance engine and platform registry...",
            "stats": {},
            "error": None
        }
        _TASKS[clean_target] = task_record

        # Spawn background thread
        worker_thread = threading.Thread(
            target=_run_recon_worker,
            args=(clean_target, scope, category, timeout, id_type, enrich, with_domains, recursive, tor),
            daemon=True
        )
        worker_thread.start()

        return _safe_task_dict(task_record)

def get_recon_status(target: str) -> Dict[str, Any]:
    """Retrieves live or cached reconnaissance state for target."""
    clean_target = target.strip()
    if clean_target in _TASKS:
        t = _TASKS[clean_target]
        elapsed = round(time.time() - t["start_time"], 1) if t["status"] == "RUNNING" else t.get("duration", 0)
        return {
            "target": clean_target,
            "status": t["status"],
            "cached": bool(t.get("cached", False)),
            "elapsed": elapsed,
            "total_sites": t.get("total_sites", 500),
            "discovered_count": t.get("discovered_count", 0),
            "discovered_items": t.get("discovered_items", [])[-8:],  # latest discoveries
            "progress_msg": t.get("progress_msg", ""),
            "findings": t.get("findings", []),
            "stats": t.get("stats", {}),
            "error": t.get("error")
        }

    # Check on-disk cache
    cached = load_cached_report_from_disk(clean_target)
    if cached:
        return {
            "target": clean_target,
            "status": "COMPLETED",
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

def get_search_history() -> List[Dict[str, Any]]:
    """Scans the reports directory and returns a sorted history of past target investigations."""
    history = []
    if not REPORTS_DIR.exists():
        return history

    for json_file in REPORTS_DIR.glob("report_*_simple.json"):
        filename = json_file.name
        # Match pattern: report_<target>_simple.json
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
                html_file = REPORTS_DIR / f"report_{target}_plain.html"
                md_file = REPORTS_DIR / f"report_{target}.md"
                history.append({
                    "target": target,
                    "count": count,
                    "timestamp": time_str,
                    "mtime": mtime,
                    "has_csv": csv_file.exists(),
                    "has_html": html_file.exists(),
                    "has_md": md_file.exists()
                })
            except Exception:
                pass

    history.sort(key=lambda x: x["mtime"], reverse=True)
    return history

def get_latest_findings(target: Optional[str] = None) -> List[Dict[str, Any]]:
    """Legacy helper returning findings list."""
    if target:
        cached = _CACHED_RESULTS.get(target) or load_cached_report_from_disk(target)
        if cached:
            return cached.get("findings", [])
    if _CACHED_RESULTS:
        return list(_CACHED_RESULTS.values())[-1].get("findings", [])
    return []

def ensure_report_file(target: str, fmt: str) -> Optional[Path]:
    """Ensures requested report file exists on disk, compiling it dynamically if missing."""
    clean_target = target.strip()
    fmt = fmt.lower().strip()

    if fmt == "csv":
        p = REPORTS_DIR / f"report_{clean_target}.csv"
        if p.exists():
            return p
        cached = load_cached_report_from_disk(clean_target)
        if not cached or not cached.get("findings"):
            return None
        import csv
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Platform", "URL", "Status", "Fullname", "Bio", "Location", "Followers", "Tags"])
            for itm in cached["findings"]:
                writer.writerow([
                    itm.get("platform", ""),
                    itm.get("url", ""),
                    itm.get("status", "Claimed"),
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
        cached = load_cached_report_from_disk(clean_target)
        if not cached or not cached.get("findings"):
            return None
        lines = [
            f"# OASIS Username Intelligence Dossier: {clean_target}",
            f"",
            f"- **Target Handle:** `{clean_target}`",
            f"- **Claimed Profiles:** {cached.get('total_claimed', len(cached['findings']))}",
            f"- **Enriched Profiles:** {cached.get('enriched_count', 0)}",
            f"- **Generated Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## Verified Profiles & Discoveries",
            f"",
            f"| # | Platform | Verified URL | Enriched Metadata |",
            f"|---|---|---|---|"
        ]
        for idx, itm in enumerate(cached["findings"], 1):
            meta_parts = []
            if itm.get("fullname"): meta_parts.append(f"**Name:** {itm['fullname']}")
            if itm.get("bio"): meta_parts.append(f"**Bio:** {itm['bio']}")
            if itm.get("location"): meta_parts.append(f"**Location:** {itm['location']}")
            if itm.get("followers"): meta_parts.append(f"**Followers:** {itm['followers']}")
            meta_str = " <br> ".join(meta_parts) if meta_parts else "Active Profile Verified"
            lines.append(f"| {idx} | **{itm.get('platform')}** | [{itm.get('url')}]({itm.get('url')}) | {meta_str} |")
        lines.append("")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return p

    elif fmt == "html":
        p = REPORTS_DIR / f"report_{clean_target}_plain.html"
        if p.exists():
            return p
        cached = load_cached_report_from_disk(clean_target)
        if not cached or not cached.get("findings"):
            return None
        rows = []
        for idx, itm in enumerate(cached["findings"], 1):
            rows.append(f"""
            <tr>
                <td>{idx}</td>
                <td><strong>{itm.get('platform')}</strong></td>
                <td><a href="{itm.get('url')}" target="_blank">{itm.get('url')}</a></td>
                <td>{itm.get('fullname', '')}</td>
                <td>{itm.get('bio', '')}</td>
                <td>{', '.join(itm.get('tags', []))}</td>
            </tr>
            """)
        html_code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OASIS Intelligence Dossier - {clean_target}</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>body {{ padding: 30px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; }} .table {{ background: #fff; border-radius: 8px; overflow: hidden; }}</style>
</head>
<body>
    <div class="container">
        <h2 class="mb-2">OASIS Intelligence Dossier: {clean_target}</h2>
        <p class="text-muted">Total Claimed Profiles: {cached.get('total_claimed', len(cached['findings']))} | Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table class="table table-bordered table-striped mt-4">
            <thead class="thead-dark">
                <tr><th>#</th><th>Platform</th><th>Verified Profile URL</th><th>Full Name</th><th>Bio / Dossier</th><th>Tags</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </div>
</body>
</html>"""
        with open(p, "w", encoding="utf-8") as f:
            f.write(html_code)
        return p

    elif fmt == "txt":
        p = REPORTS_DIR / f"report_{clean_target}.txt"
        if p.exists():
            return p
        cached = load_cached_report_from_disk(clean_target)
        if not cached or not cached.get("findings"):
            return None
        lines = [f"OASIS Reconnaissance Report for: {clean_target}", "=" * 50]
        for itm in cached["findings"]:
            lines.append(f"[{itm.get('platform')}] {itm.get('url')}")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return p

    elif fmt == "json":
        p = REPORTS_DIR / f"report_{clean_target}_simple.json"
        if p.exists():
            return p
        return None

    return None
