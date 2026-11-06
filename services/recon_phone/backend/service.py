import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_phone.tools.carrier_lookup.engine import run_engine as run_carrier_lookup
from services.recon_phone.tools.hlr_validator.engine import run_engine as run_hlr_validator
from services.recon_phone.tools.line_type_detector.engine import run_engine as run_line_type_detector

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['carrier_lookup', 'hlr_validator', 'line_type_detector']
    
    add_log("Phone Number Recon & Carrier Intelligence", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Phone Number Recon & Carrier Intelligence",
        status="PROCESSING",
        title="Phone Number Recon & Carrier Intelligence Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-phone"
    )

    findings = []
    try:
        if "carrier_lookup" in tools:
            add_log("Phone Number Recon & Carrier Intelligence", "Launching sub-engine: Carrier & Telco Lookup on " + target, "info")
            findings.extend(run_carrier_lookup(target, {"profile": profile}))
        if "hlr_validator" in tools:
            add_log("Phone Number Recon & Carrier Intelligence", "Launching sub-engine: HLR Network Validator on " + target, "info")
            findings.extend(run_hlr_validator(target, {"profile": profile}))
        if "line_type_detector" in tools:
            add_log("Phone Number Recon & Carrier Intelligence", "Launching sub-engine: Line Type & Format Detector on " + target, "info")
            findings.extend(run_line_type_detector(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Phone Number Recon & Carrier Intelligence",
            target=target,
            new_status="FINISHED",
            title="Phone Number Recon & Carrier Intelligence Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Phone Number Recon & Carrier Intelligence", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Phone Number Recon & Carrier Intelligence", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Phone Number Recon & Carrier Intelligence",
            target=target,
            new_status="FINISHED",
            title="Phone Number Recon & Carrier Intelligence Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
