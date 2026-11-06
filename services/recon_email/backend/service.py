import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_email.tools.breach_scanner.engine import run_engine as run_breach_scanner
from services.recon_email.tools.smtp_validator.engine import run_engine as run_smtp_validator
from services.recon_email.tools.domain_mail_finder.engine import run_engine as run_domain_mail_finder

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['breach_scanner', 'smtp_validator', 'domain_mail_finder']
    
    add_log("Email Address Scraping & Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Email Address Scraping & Recon",
        status="PROCESSING",
        title="Email Address Scraping & Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-email"
    )

    findings = []
    try:
        if "breach_scanner" in tools:
            add_log("Email Address Scraping & Recon", "Launching sub-engine: Breach & Leak Scanner on " + target, "info")
            findings.extend(run_breach_scanner(target, {"profile": profile}))
        if "smtp_validator" in tools:
            add_log("Email Address Scraping & Recon", "Launching sub-engine: SMTP & MX Validator on " + target, "info")
            findings.extend(run_smtp_validator(target, {"profile": profile}))
        if "domain_mail_finder" in tools:
            add_log("Email Address Scraping & Recon", "Launching sub-engine: Domain Mail Finder on " + target, "info")
            findings.extend(run_domain_mail_finder(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Email Address Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="Email Address Scraping & Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Email Address Scraping & Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Email Address Scraping & Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Email Address Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="Email Address Scraping & Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
