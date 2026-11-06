import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.social_linkedin.tools.profile_recon.engine import run_engine as run_profile_recon
from services.social_linkedin.tools.company_intelligence.engine import run_engine as run_company_intelligence
from services.social_linkedin.tools.workforce_mapper.engine import run_engine as run_workforce_mapper

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['profile_recon', 'company_intelligence', 'workforce_mapper']
    
    add_log("LinkedIn Intelligence & Scraping", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="LinkedIn Intelligence & Scraping",
        status="PROCESSING",
        title="LinkedIn Intelligence & Scraping Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/social-linkedin"
    )

    findings = []
    try:
        if "profile_recon" in tools:
            add_log("LinkedIn Intelligence & Scraping", "Launching sub-engine: Profile Recon Engine on " + target, "info")
            findings.extend(run_profile_recon(target, {"profile": profile}))
        if "company_intelligence" in tools:
            add_log("LinkedIn Intelligence & Scraping", "Launching sub-engine: Company Intelligence on " + target, "info")
            findings.extend(run_company_intelligence(target, {"profile": profile}))
        if "workforce_mapper" in tools:
            add_log("LinkedIn Intelligence & Scraping", "Launching sub-engine: Workforce Mapper on " + target, "info")
            findings.extend(run_workforce_mapper(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="LinkedIn Intelligence & Scraping",
            target=target,
            new_status="FINISHED",
            title="LinkedIn Intelligence & Scraping Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("LinkedIn Intelligence & Scraping", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("LinkedIn Intelligence & Scraping", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="LinkedIn Intelligence & Scraping",
            target=target,
            new_status="FINISHED",
            title="LinkedIn Intelligence & Scraping Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
