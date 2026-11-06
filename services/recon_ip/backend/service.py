import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_ip.tools.geoip_locator.engine import run_engine as run_geoip_locator
from services.recon_ip.tools.asn_enumerator.engine import run_engine as run_asn_enumerator
from services.recon_ip.tools.reverse_dns.engine import run_engine as run_reverse_dns

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['geoip_locator', 'asn_enumerator', 'reverse_dns']
    
    add_log("IP Address Intelligence & Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="IP Address Intelligence & Recon",
        status="PROCESSING",
        title="IP Address Intelligence & Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-ip"
    )

    findings = []
    try:
        if "geoip_locator" in tools:
            add_log("IP Address Intelligence & Recon", "Launching sub-engine: GeoIP Locator on " + target, "info")
            findings.extend(run_geoip_locator(target, {"profile": profile}))
        if "asn_enumerator" in tools:
            add_log("IP Address Intelligence & Recon", "Launching sub-engine: ASN & BGP Enumerator on " + target, "info")
            findings.extend(run_asn_enumerator(target, {"profile": profile}))
        if "reverse_dns" in tools:
            add_log("IP Address Intelligence & Recon", "Launching sub-engine: Reverse DNS & SSL Pointer on " + target, "info")
            findings.extend(run_reverse_dns(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="IP Address Intelligence & Recon",
            target=target,
            new_status="FINISHED",
            title="IP Address Intelligence & Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("IP Address Intelligence & Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("IP Address Intelligence & Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="IP Address Intelligence & Recon",
            target=target,
            new_status="FINISHED",
            title="IP Address Intelligence & Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
