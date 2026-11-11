import json
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from core.config import BASE_DIR
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification


MODULES: Dict[str, Dict[str, Any]] = {
    "website-url": {
        "view": "recon_website_url",
        "title": "Website Surface Intelligence",
        "route": "/services/recon-website-url",
        "summary": "Map public web surface, application routes, assets, and exposed intelligence from a target domain.",
        "features": [
            "Recursive internal and external URL discovery",
            "robots.txt and sitemap.xml collection",
            "JavaScript endpoint and API route extraction",
            "Document, media, script, and downloadable asset inventory",
            "Email, social profile, cloud bucket, and custom-pattern discovery",
            "High-entropy secret and API-key exposure detection",
            "Query-parameter and fuzzable URL identification",
            "Wayback Machine seed collection with JSON and CSV export",
        ],
        "defaults": {"level": 2, "threads": 8, "keys": True},
    },
    "subdomains": {
        "view": "recon_subdomains",
        "title": "Hostname & Subdomain Intelligence",
        "route": "/services/recon-subdomains",
        "summary": "Expand a root domain into a structured inventory of public hostnames and DNS-linked infrastructure.",
        "features": [
            "Subdomain discovery using curated DNS enumeration",
            "DNSDumpster-assisted infrastructure mapping",
            "Hostname collection from linked public pages",
            "Resolution-ready output for downstream validation",
            "Optional recursive crawl of discovered web surfaces",
            "Structured findings suitable for the target repository",
        ],
        "defaults": {"level": 1, "threads": 8, "dns": True},
    },
    "web-browsers": {
        "view": "recon_web_browsers",
        "title": "Web Footprint Intelligence",
        "route": "/services/recon-web-browsers",
        "summary": "Collect the public application footprint that informs browser, technology, and defensive-posture review.",
        "features": [
            "HTML and response-content collection across linked pages",
            "Script inventory and client-side endpoint extraction",
            "External dependency and referenced-host mapping",
            "Technology clues from headers, metadata, and resource paths",
            "Security-relevant strings and configuration exposure detection",
            "Exportable evidence for browser and DOM review workflows",
        ],
        "defaults": {"level": 2, "threads": 6},
    },
}

_JOBS: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.Lock()


def get_module(module: str) -> Dict[str, Any]:
    try:
        return MODULES[module]
    except KeyError as exc:
        raise ValueError(f"Unknown surface analysis module: {module}") from exc


def _validate_target(target: str) -> str:
    value = target.strip()
    if not value:
        raise ValueError("A target URL or domain is required.")
    candidate = value if re.match(r"^https?://", value, re.IGNORECASE) else f"https://{value}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(char.isspace() for char in parsed.netloc):
        raise ValueError("Enter a valid HTTP(S) URL or domain.")
    return candidate


def _worker(job_id: str, module: str, target: str, options: Dict[str, Any]) -> None:
    config = get_module(module)
    output_dir = BASE_DIR / ".data" / "surface-scans" / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    engine_dir = BASE_DIR.parent / "Photon_osint_url"
    command = [
        sys.executable,
        str(engine_dir / "photon.py"),
        "-u",
        target,
        "-e",
        "json",
        "-o",
        str(output_dir),
        "-l",
        str(options.get("level", config["defaults"].get("level", 2))),
        "-t",
        str(options.get("threads", config["defaults"].get("threads", 6))),
    ]
    if options.get("keys", config["defaults"].get("keys", False)):
        command.append("--keys")
    if options.get("dns", config["defaults"].get("dns", False)):
        command.append("--dns")
    if options.get("wayback"):
        command.append("--wayback")
    if options.get("only_urls"):
        command.append("--only-urls")
    if options.get("exclude"):
        command.extend(["--exclude", str(options["exclude"])])
    if options.get("regex"):
        command.extend(["-r", str(options["regex"])])

    with _LOCK:
        _JOBS[job_id]["status"] = "running"
        _JOBS[job_id]["command"] = command
    add_log(config["title"], f"Started analysis for {target}", "info")

    try:
        completed = subprocess.run(
            command,
            cwd=str(engine_dir),
            capture_output=True,
            text=True,
            timeout=options.get("timeout", 900),
            check=False,
        )
        export_path = output_dir / "exported.json"
        results: Dict[str, List[str]] = {}
        if export_path.exists():
            with export_path.open("r", encoding="utf-8") as export_file:
                results = json.load(export_file)
        if completed.returncode != 0:
            error = completed.stderr.strip() or completed.stdout.strip()[-1000:] or "Analysis process failed."
            raise RuntimeError(error)
        with _LOCK:
            _JOBS[job_id].update(
                status="completed",
                results=results,
                output_dir=str(output_dir),
                summary={key: len(value or []) for key, value in results.items()},
                logs=completed.stdout.splitlines()[-80:],
            )
        update_tool_notification(
            config["title"],
            target,
            "FINISHED",
            title=f"{config['title']} completed",
            details="The requested public-surface analysis is ready for review.",
            metrics=f"{sum(len(value or []) for value in results.values())} observations",
        )
        add_log(config["title"], f"Completed analysis for {target}", "success")
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        with _LOCK:
            _JOBS[job_id].update(status="failed", error=str(exc))
        update_tool_notification(
            config["title"],
            target,
            "FINISHED",
            title=f"{config['title']} failed",
            details=str(exc),
        )
        add_log(config["title"], str(exc), "error")


def start_analysis(module: str, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = get_module(module)
    normalized_target = _validate_target(target)
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "module": module,
        "title": config["title"],
        "target": normalized_target,
        "status": "queued",
        "results": {},
        "summary": {},
        "logs": [],
    }
    with _LOCK:
        _JOBS[job_id] = job
    add_recon_notification(
        tool=config["title"],
        status="PROCESSING",
        title=f"{config['title']} started",
        details=f"Collecting public intelligence for {normalized_target}.",
        target=normalized_target,
        action_url=config["route"],
    )
    threading.Thread(
        target=_worker,
        args=(job_id, module, normalized_target, options or {}),
        daemon=True,
        name=f"oasis-surface-{module}",
    ).start()
    return job


def get_job(job_id: str) -> Dict[str, Any]:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise ValueError("Analysis job was not found.")
        return dict(job)


def list_jobs(module: str) -> List[Dict[str, Any]]:
    with _LOCK:
        return [dict(job) for job in reversed(list(_JOBS.values())) if job["module"] == module][:20]
