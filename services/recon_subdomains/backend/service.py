import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_subdomains.tools.dns_bruteforce.engine import run_engine as run_dns_bruteforce
from services.recon_subdomains.tools.certificate_transparency.engine import run_engine as run_certificate_transparency
from services.recon_subdomains.tools.zone_enumerator.engine import run_engine as run_zone_enumerator

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['dns_bruteforce', 'certificate_transparency', 'zone_enumerator']
    
    add_log("Hostname & Subdomain Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Hostname & Subdomain Recon",
        status="PROCESSING",
        title="Hostname & Subdomain Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-subdomains"
    )

    findings = []
    try:
        if "dns_bruteforce" in tools:
            add_log("Hostname & Subdomain Recon", "Launching sub-engine: DNS Bruteforce Resolver on " + target, "info")
            findings.extend(run_dns_bruteforce(target, {"profile": profile}))
        if "certificate_transparency" in tools:
            add_log("Hostname & Subdomain Recon", "Launching sub-engine: Certificate Transparency Indexer on " + target, "info")
            findings.extend(run_certificate_transparency(target, {"profile": profile}))
        if "zone_enumerator" in tools:
            add_log("Hostname & Subdomain Recon", "Launching sub-engine: Zone & Record Enumerator on " + target, "info")
            findings.extend(run_zone_enumerator(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Hostname & Subdomain Recon",
            target=target,
            new_status="FINISHED",
            title="Hostname & Subdomain Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Hostname & Subdomain Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Hostname & Subdomain Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Hostname & Subdomain Recon",
            target=target,
            new_status="FINISHED",
            title="Hostname & Subdomain Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
