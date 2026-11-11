import os
import sys
import time
import json
import re
import uuid
import threading
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

from core.config import BASE_DIR
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

# Reports and Output Storage Directory
REPORTS_DIR = BASE_DIR / "services" / "domain_intelligence" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Locate Photon engine script
ENGINE_DIR = (BASE_DIR.parent / "Photon_osint_url").resolve()
ENGINE_SCRIPT = ENGINE_DIR / "photon.py"

# Use Photon virtualenv or Oasis virtualenv python
def _get_domain_engine_python() -> str:
    cand = ENGINE_DIR / "venv" / "bin" / "python"
    if cand.exists():
        return str(cand)
    cand2 = BASE_DIR / ".venv" / "bin" / "python"
    if cand2.exists():
        return str(cand2)
    return sys.executable

ENGINE_PYTHON = _get_domain_engine_python()

_JOBS: Dict[str, Dict[str, Any]] = {}
_DOMAIN_CACHE: Dict[str, Dict[str, Any]] = {}
_DOMAIN_PROCESSES: Dict[str, subprocess.Popen] = {}
_LOCK = threading.Lock()

def _safe_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """Returns a JSON-serializable snapshot of a job."""
    return {
        "job_id": job.get("job_id", ""),
        "target": job.get("target", ""),
        "domain": job.get("domain", ""),
        "status": job.get("status", "IDLE"),
        "cached": bool(job.get("cached", False)),
        "duration": job.get("duration", 0),
        "elapsed": job.get("elapsed", 0),
        "progress_msg": job.get("progress_msg", ""),
        "stats": job.get("stats", {}),
        "findings": job.get("findings", []),
        "error": job.get("error")
    }

def sanitize_text(text: str) -> str:
    """Removes internal tool brand names from output logs."""
    if not text:
        return ""
    import re
    cleaned = re.sub(r'(?i)photon', 'Domain Reconnaissance Engine', text)
    return cleaned

def normalize_domain_target(target: str) -> str:
    """Normalizes domain target into clean http/https URL."""
    val = target.strip()
    if not val:
        raise ValueError("Target domain or URL cannot be empty.")
    if not val.startswith("http://") and not val.startswith("https://"):
        val = f"https://{val}"
    parsed = urlparse(val)
    if not parsed.netloc:
        raise ValueError("Invalid target format. Enter a valid domain (e.g. example.com) or URL.")
    return val

def _categorize_intel_item(item: str) -> Dict[str, str]:
    """Classifies an extracted intel string into email, social profile, or cloud bucket."""
    val = item.strip()
    val_lower = val.lower()
    if "@" in val and not "/" in val:
        return {"category": "Email Address", "badge": "EMAIL", "badge_color": "#2563eb", "value": val}
    if any(s in val_lower for s in ["twitter.com", "x.com", "linkedin.com", "facebook.com", "instagram.com", "github.com", "youtube.com"]):
        return {"category": "Social Media Profile", "badge": "SOCIAL", "badge_color": "#8b5cf6", "value": val}
    if any(s in val_lower for s in ["s3.amazonaws.com", "storage.googleapis.com", "blob.core.windows.net"]):
        return {"category": "Cloud Storage Bucket", "badge": "CLOUD", "badge_color": "#ea580c", "value": val}
    return {"category": "Public Identifier", "badge": "INTEL", "badge_color": "#059669", "value": val}

def _parse_scan_output(output_dir: Path, target: str) -> Dict[str, Any]:
    """Parses exported.json and companion output files into structured OASIS findings."""
    json_path = output_dir / "exported.json"
    raw_data = {}
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            pass

    def _read_lines(fname: str) -> List[str]:
        p = output_dir / fname
        if not p.exists():
            return []
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    # Extract arrays from json or fallback to text files
    internal_urls = raw_data.get("internal", []) or _read_lines("internal.txt")
    external_urls = raw_data.get("external", []) or _read_lines("external.txt")
    fuzzable_urls = raw_data.get("fuzzable", []) or _read_lines("fuzzable.txt")
    endpoints = raw_data.get("endpoints", []) or _read_lines("endpoints.txt")
    scripts = raw_data.get("scripts", []) or _read_lines("scripts.txt")
    subdomains = raw_data.get("subdomains", []) or _read_lines("subdomains.txt")
    files = raw_data.get("files", []) or _read_lines("files.txt")
    intel_raw = raw_data.get("intel", []) or _read_lines("intel.txt")
    keys = raw_data.get("keys", []) or _read_lines("keys.txt")
    robots = raw_data.get("robots", []) or _read_lines("robots.txt")

    # Deduplicate arrays
    internal_urls = list(dict.fromkeys(internal_urls))
    external_urls = list(dict.fromkeys(external_urls))
    fuzzable_urls = list(dict.fromkeys(fuzzable_urls))
    endpoints = list(dict.fromkeys(endpoints))
    scripts = list(dict.fromkeys(scripts))
    subdomains = list(dict.fromkeys(subdomains))
    files = list(dict.fromkeys(files))
    intel_raw = list(dict.fromkeys(intel_raw))
    keys = list(dict.fromkeys(keys))

    # Detect mailto: emails inside discovered URLs
    for u in internal_urls + external_urls:
        if "mailto:" in u:
            m = re.search(r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', u)
            if m:
                extracted_email = m.group(1)
                if extracted_email not in intel_raw:
                    intel_raw.append(extracted_email)

    # If exported.json didn't exist, generate one from the discovered datasets
    if not json_path.exists():
        try:
            exported_payload = {
                "internal": internal_urls,
                "external": external_urls,
                "fuzzable": fuzzable_urls,
                "endpoints": endpoints,
                "scripts": scripts,
                "subdomains": subdomains,
                "files": files,
                "intel": intel_raw,
                "keys": keys,
                "robots": robots
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(exported_payload, f, indent=2)
        except Exception:
            pass

    # Extract classified findings
    classified_findings = []

    # 1. Subdomains
    for s in subdomains:
        if s:
            classified_findings.append({
                "type": "SUBDOMAIN",
                "category": "DNS Infrastructure",
                "badge": "DNS",
                "value": s,
                "detail": "Discovered Hostname"
            })

    # 2. Intel (Emails, Social, Buckets)
    for itm in intel_raw:
        if itm:
            cat_info = _categorize_intel_item(itm)
            classified_findings.append({
                "type": "INTEL",
                "category": cat_info["category"],
                "badge": cat_info["badge"],
                "value": cat_info["value"],
                "detail": "Harvested Identity / Asset"
            })

    # 3. Exposed Keys & Secrets
    for k in keys:
        if k:
            classified_findings.append({
                "type": "SECRET",
                "category": "Exposed Credential / Secret",
                "badge": "KEY",
                "value": k,
                "detail": "High-Entropy Token / API Key"
            })

    # 4. Fuzzable URLs (URLs with query params)
    for u in fuzzable_urls:
        if u:
            classified_findings.append({
                "type": "URL",
                "category": "Fuzzable URL Parameter",
                "badge": "PARAM",
                "value": u,
                "detail": "Dynamic GET Parameters"
            })

    # 5. In-Scope Internal URLs
    for u in internal_urls:
        if u and u not in fuzzable_urls:
            classified_findings.append({
                "type": "URL",
                "category": "Internal In-Scope Route",
                "badge": "ROUTE",
                "value": u,
                "detail": "Web Surface Endpoint"
            })

    # 6. JavaScript Endpoints
    for ep in endpoints:
        if ep:
            classified_findings.append({
                "type": "ENDPOINT",
                "category": "Client-Side Script Route",
                "badge": "JS-API",
                "value": ep,
                "detail": "Extracted from Scripts"
            })

    # 7. Static Files
    for fl in files:
        if fl:
            classified_findings.append({
                "type": "FILE",
                "category": "Downloadable Document / Asset",
                "badge": "FILE",
                "value": fl,
                "detail": "Discovered Static File"
            })

    # 8. External URLs
    for eu in external_urls[:100]:
        if eu:
            classified_findings.append({
                "type": "URL",
                "category": "Referenced External URL",
                "badge": "EXTERNAL",
                "value": eu,
                "detail": "Outbound Reference"
            })

    stats = {
        "total_urls": len(internal_urls) + len(external_urls),
        "internal_count": len(internal_urls),
        "fuzzable_count": len(fuzzable_urls),
        "subdomain_count": len(subdomains),
        "intel_count": len(intel_raw),
        "secret_count": len(keys),
        "file_count": len(files),
        "endpoint_count": len(endpoints),
    }

    return {
        "target": target,
        "stats": stats,
        "findings": classified_findings,
        "files": {
            "json": str(json_path),
            "output_dir": str(output_dir)
        }
    }

def _run_domain_worker(job_id: str, target_url: str, depth: int, threads: int, dns: bool, keys: bool, wayback: bool):
    """Executes the Domain & Website Intelligence engine via background worker."""
    job = _JOBS[job_id]
    job_output_dir = REPORTS_DIR / job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        ENGINE_PYTHON,
        str(ENGINE_SCRIPT),
        "-u", target_url,
        "-e", "json",
        "-o", str(job_output_dir),
        "-l", str(depth),
        "-t", str(threads),
    ]

    if keys:
        cmd.append("--keys")
    if dns:
        cmd.append("--dns")
    if wayback:
        cmd.append("--wayback")

    add_log("Domain Intelligence", f"Launching domain intelligence crawler on {target_url} (Depth: {depth}, Threads: {threads})", "info")
    add_recon_notification(
        tool="Domain & Website Intelligence",
        status="PROCESSING",
        title="Domain Intelligence Query Initiated",
        details=f"Spidering web surface, hostnames, and secrets for: {target_url}",
        target=target_url,
        action_url="/services/domain-intelligence"
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(ENGINE_DIR)
        )
        _DOMAIN_PROCESSES[job_id] = proc

        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            line_str = line.strip()
            if line_str.startswith("[~]") or line_str.startswith("[+]") or line_str.startswith("[!]"):
                clean_msg = sanitize_text(line_str)
                job["progress_msg"] = clean_msg
                if "URLs" in clean_msg or "requests" in clean_msg:
                    job["last_activity"] = clean_msg

        proc.wait()

        # Parse final structured results
        parsed = _parse_scan_output(job_output_dir, target_url)
        
        domain_key = urlparse(target_url).netloc
        _DOMAIN_CACHE[domain_key] = parsed

        job["status"] = "COMPLETED"
        job["duration"] = round(time.time() - job["start_time"], 1)
        job["findings"] = parsed["findings"]
        job["stats"] = parsed["stats"]
        job["progress_msg"] = f"Domain analysis completed. {len(parsed['findings'])} intelligence observations indexed."

        # Save metadata for search history
        try:
            meta = {
                "job_id": job_id,
                "target": target_url,
                "domain": domain_key,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": job["duration"],
                "stats": parsed["stats"],
                "total_findings": len(parsed["findings"])
            }
            with open(job_output_dir / "meta.json", "w", encoding="utf-8") as mf:
                json.dump(meta, mf, indent=2)
        except Exception:
            pass

        update_tool_notification(
            tool="Domain & Website Intelligence",
            target=target_url,
            new_status="FINISHED",
            title="Domain & Website Intelligence Completed",
            details=f"Harvested {parsed['stats']['total_urls']} endpoints, {parsed['stats']['subdomain_count']} subdomains, and {parsed['stats']['secret_count']} secrets.",
            metrics=f"{parsed['stats']['total_urls']} URLs • {parsed['stats']['subdomain_count']} Subdomains • {parsed['stats']['intel_count']} Contacts"
        )
        add_log("Domain Intelligence", f"Completed domain reconnaissance for {target_url}: {len(parsed['findings'])} observations in {job['duration']}s.", "success")

    except Exception as e:
        job["status"] = "ERROR"
        job["error"] = sanitize_text(str(e))
        job["duration"] = round(time.time() - job["start_time"], 1)
        add_log("Domain Intelligence", f"Error during domain crawling: {e}", "error")
        update_tool_notification(
            tool="Domain & Website Intelligence",
            target=target_url,
            new_status="FINISHED",
            title="Domain Intelligence Error",
            details=sanitize_text(str(e))
        )
    finally:
        _DOMAIN_PROCESSES.pop(job_id, None)

def execute_domain_task(
    target: str,
    depth: int = 2,
    threads: int = 8,
    dns: bool = True,
    keys: bool = True,
    wayback: bool = False,
    force: bool = False
) -> Dict[str, Any]:
    """Initiates a domain & website intelligence task."""
    normalized_target = normalize_domain_target(target)
    domain_key = urlparse(normalized_target).netloc

    # Check cache if not forcing re-crawl
    if not force and domain_key in _DOMAIN_CACHE:
        cached = _DOMAIN_CACHE[domain_key]
        return {
            "job_id": "cached_" + domain_key,
            "target": normalized_target,
            "status": "COMPLETED",
            "cached": True,
            "duration": 0.1,
            "stats": cached["stats"],
            "findings": cached["findings"],
            "progress_msg": "Loaded cached domain observations."
        }

    with _LOCK:
        job_id = uuid.uuid4().hex[:12]
        job = {
            "job_id": job_id,
            "target": normalized_target,
            "domain": domain_key,
            "status": "RUNNING",
            "start_time": time.time(),
            "duration": 0,
            "progress_msg": f"Initializing domain crawler for {domain_key}...",
            "stats": {},
            "findings": [],
            "error": None
        }
        _JOBS[job_id] = job

        worker = threading.Thread(
            target=_run_domain_worker,
            args=(job_id, normalized_target, depth, threads, dns, keys, wayback),
            daemon=True
        )
        worker.start()

        return _safe_job_dict(job)

def get_domain_status(job_id: str) -> Dict[str, Any]:
    """Retrieves live job status and findings."""
    clean_id = job_id.strip()
    if clean_id in _JOBS:
        j = _JOBS[clean_id]
        elapsed = round(time.time() - j["start_time"], 1) if j["status"] == "RUNNING" else j.get("duration", 0)
        return {
            "job_id": clean_id,
            "target": j["target"],
            "status": j["status"],
            "elapsed": elapsed,
            "progress_msg": j.get("progress_msg", ""),
            "stats": j.get("stats", {}),
            "findings": j.get("findings", []),
            "error": j.get("error")
        }
    
    # Check domain cache if clean_id is a domain
    if clean_id in _DOMAIN_CACHE:
        cached = _DOMAIN_CACHE[clean_id]
        return {
            "job_id": "cached_" + clean_id,
            "target": cached["target"],
            "status": "COMPLETED",
            "elapsed": 0,
            "progress_msg": "Completed.",
            "stats": cached["stats"],
            "findings": cached["findings"],
            "error": None
        }

    return {
        "job_id": clean_id,
        "status": "IDLE",
        "elapsed": 0,
        "progress_msg": "Awaiting scan.",
        "stats": {},
        "findings": [],
        "error": None
    }

def get_domain_history() -> List[Dict[str, Any]]:
    """Scans domain reports directory and returns past domain scans."""
    history = []
    if not REPORTS_DIR.exists():
        return history

    for folder in REPORTS_DIR.iterdir():
        if folder.is_dir():
            meta_file = folder / "meta.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["mtime"] = meta_file.stat().st_mtime
                        history.append(data)
                        continue
                except Exception:
                    pass

            # Fallback if meta.json doesn't exist yet but folder has files
            txt_files = list(folder.glob("*.txt")) + list(folder.glob("*.json"))
            if txt_files:
                mtime = max(f.stat().st_mtime for f in txt_files)
                # Parse folder
                target_name = folder.name
                history.append({
                    "job_id": folder.name,
                    "target": target_name,
                    "domain": target_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
                    "duration": 0,
                    "stats": {},
                    "total_findings": len(txt_files),
                    "mtime": mtime
                })

    history.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return history

def find_domain_job_dir(identifier: str) -> Optional[Path]:
    """Finds the output directory for a given job_id or target domain."""
    clean = identifier.strip()
    if not clean:
        return None

    # Check direct folder match
    direct = REPORTS_DIR / clean
    if direct.exists() and direct.is_dir():
        return direct

    # Search through subfolders
    for folder in REPORTS_DIR.iterdir():
        if not folder.is_dir():
            continue
        if folder.name.lower() == clean.lower():
            return folder
        meta_file = folder / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if (
                        meta.get("target", "").lower() == clean.lower()
                        or meta.get("domain", "").lower() == clean.lower()
                        or meta.get("clean_target", "").lower() == clean.lower()
                    ):
                        return folder
            except Exception:
                pass
    return None

def ensure_domain_report_file(identifier: str, fmt: str = "json") -> Optional[Path]:
    """Ensures that a requested report format (JSON, TXT, CSV) exists on disk."""
    folder = find_domain_job_dir(identifier)
    if not folder:
        return None

    fmt = fmt.lower().strip()
    target_name = folder.name
    meta_file = folder / "meta.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                target_name = meta.get("target") or meta.get("domain") or folder.name
        except Exception:
            pass

    if fmt == "json":
        json_path = folder / "exported.json"
        if not json_path.exists():
            _parse_scan_output(folder, target_name)
        if json_path.exists():
            return json_path
        parsed = _parse_scan_output(folder, target_name)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
        return json_path

    elif fmt == "csv":
        csv_path = folder / "domain_intel.csv"
        parsed = _parse_scan_output(folder, target_name)
        findings = parsed.get("findings", [])
        import csv
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Target Domain", "Category", "Badge", "Discovered Observation / Value"])
            for item in findings:
                writer.writerow([
                    target_name,
                    item.get("category", ""),
                    item.get("badge", ""),
                    item.get("value", "")
                ])
        return csv_path

    else:  # txt
        txt_path = folder / "domain_inventory.txt"
        parsed = _parse_scan_output(folder, target_name)
        findings = parsed.get("findings", [])
        lines = [
            "=== OASIS DOMAIN & WEBSITE INTELLIGENCE INVENTORY ===",
            f"Target: {target_name}",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Discoveries: {len(findings)}",
            "",
            "--- DETAILED FINDINGS ---"
        ]
        for item in findings:
            lines.append(f"[{item.get('badge', 'INTEL')}] ({item.get('category', 'General')}) {item.get('value', '')}")
        
        internal_file = folder / "internal.txt"
        if internal_file.exists():
            try:
                lines.append("\n--- INTERNAL CRAWLED ROUTES ---")
                lines.append(internal_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        return txt_path

