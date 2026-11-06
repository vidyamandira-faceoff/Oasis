import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_username.tools.cross_platform_scanner.engine import run_engine as run_cross_platform_scanner
from services.recon_username.tools.account_enumerator.engine import run_engine as run_account_enumerator
from services.recon_username.tools.alias_correlator.engine import run_engine as run_alias_correlator

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['cross_platform_scanner', 'account_enumerator', 'alias_correlator']
    
    add_log("Username Reconnaissance & Identity", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Username Reconnaissance & Identity",
        status="PROCESSING",
        title="Username Reconnaissance & Identity Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-username"
    )

    findings = []
    try:
        if "cross_platform_scanner" in tools:
            add_log("Username Reconnaissance & Identity", "Launching sub-engine: Cross-Platform Scanner on " + target, "info")
            findings.extend(run_cross_platform_scanner(target, {"profile": profile}))
        if "account_enumerator" in tools:
            add_log("Username Reconnaissance & Identity", "Launching sub-engine: Account Profile Enumerator on " + target, "info")
            findings.extend(run_account_enumerator(target, {"profile": profile}))
        if "alias_correlator" in tools:
            add_log("Username Reconnaissance & Identity", "Launching sub-engine: Alias Correlator on " + target, "info")
            findings.extend(run_alias_correlator(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Username Reconnaissance & Identity",
            target=target,
            new_status="FINISHED",
            title="Username Reconnaissance & Identity Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Username Reconnaissance & Identity", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Username Reconnaissance & Identity", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Username Reconnaissance & Identity",
            target=target,
            new_status="FINISHED",
            title="Username Reconnaissance & Identity Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
