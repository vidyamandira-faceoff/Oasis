import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_web_browsers.tools.headless_analyzer.engine import run_engine as run_headless_analyzer
from services.recon_web_browsers.tools.tech_fingerprinter.engine import run_engine as run_tech_fingerprinter
from services.recon_web_browsers.tools.dom_inspector.engine import run_engine as run_dom_inspector

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['headless_analyzer', 'tech_fingerprinter', 'dom_inspector']
    
    add_log("Web Footprint & Browser Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Web Footprint & Browser Recon",
        status="PROCESSING",
        title="Web Footprint & Browser Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-web-browsers"
    )

    findings = []
    try:
        if "headless_analyzer" in tools:
            add_log("Web Footprint & Browser Recon", "Launching sub-engine: Headless Browser Auditor on " + target, "info")
            findings.extend(run_headless_analyzer(target, {"profile": profile}))
        if "tech_fingerprinter" in tools:
            add_log("Web Footprint & Browser Recon", "Launching sub-engine: Tech Stack Fingerprinter on " + target, "info")
            findings.extend(run_tech_fingerprinter(target, {"profile": profile}))
        if "dom_inspector" in tools:
            add_log("Web Footprint & Browser Recon", "Launching sub-engine: DOM & Header Inspector on " + target, "info")
            findings.extend(run_dom_inspector(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Web Footprint & Browser Recon",
            target=target,
            new_status="FINISHED",
            title="Web Footprint & Browser Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Web Footprint & Browser Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Web Footprint & Browser Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Web Footprint & Browser Recon",
            target=target,
            new_status="FINISHED",
            title="Web Footprint & Browser Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
