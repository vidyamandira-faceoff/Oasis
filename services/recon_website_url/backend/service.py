import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_website_url.tools.deep_crawler.engine import run_engine as run_deep_crawler
from services.recon_website_url.tools.endpoint_extractor.engine import run_engine as run_endpoint_extractor
from services.recon_website_url.tools.secret_detector.engine import run_engine as run_secret_detector

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['deep_crawler', 'endpoint_extractor', 'secret_detector']
    
    add_log("Website URL Search & Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Website URL Search & Recon",
        status="PROCESSING",
        title="Website URL Search & Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-website-url"
    )

    findings = []
    try:
        if "deep_crawler" in tools:
            add_log("Website URL Search & Recon", "Launching sub-engine: Deep Web Crawler on " + target, "info")
            findings.extend(run_deep_crawler(target, {"profile": profile}))
        if "endpoint_extractor" in tools:
            add_log("Website URL Search & Recon", "Launching sub-engine: Endpoint & API Extractor on " + target, "info")
            findings.extend(run_endpoint_extractor(target, {"profile": profile}))
        if "secret_detector" in tools:
            add_log("Website URL Search & Recon", "Launching sub-engine: Secret & Token Detector on " + target, "info")
            findings.extend(run_secret_detector(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Website URL Search & Recon",
            target=target,
            new_status="FINISHED",
            title="Website URL Search & Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Website URL Search & Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Website URL Search & Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Website URL Search & Recon",
            target=target,
            new_status="FINISHED",
            title="Website URL Search & Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
