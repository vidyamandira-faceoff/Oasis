import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.recon_crypto.tools.blockchain_explorer.engine import run_engine as run_blockchain_explorer
from services.recon_crypto.tools.wallet_profiler.engine import run_engine as run_wallet_profiler
from services.recon_crypto.tools.transaction_flow.engine import run_engine as run_transaction_flow

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['blockchain_explorer', 'wallet_profiler', 'transaction_flow']
    
    add_log("Bitcoin & Crypto Address Intelligence", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Bitcoin & Crypto Address Intelligence",
        status="PROCESSING",
        title="Bitcoin & Crypto Address Intelligence Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/recon-crypto"
    )

    findings = []
    try:
        if "blockchain_explorer" in tools:
            add_log("Bitcoin & Crypto Address Intelligence", "Launching sub-engine: Blockchain Explorer on " + target, "info")
            findings.extend(run_blockchain_explorer(target, {"profile": profile}))
        if "wallet_profiler" in tools:
            add_log("Bitcoin & Crypto Address Intelligence", "Launching sub-engine: Wallet Risk Profiler on " + target, "info")
            findings.extend(run_wallet_profiler(target, {"profile": profile}))
        if "transaction_flow" in tools:
            add_log("Bitcoin & Crypto Address Intelligence", "Launching sub-engine: Transaction Flow Grapher on " + target, "info")
            findings.extend(run_transaction_flow(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Bitcoin & Crypto Address Intelligence",
            target=target,
            new_status="FINISHED",
            title="Bitcoin & Crypto Address Intelligence Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Bitcoin & Crypto Address Intelligence", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Bitcoin & Crypto Address Intelligence", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Bitcoin & Crypto Address Intelligence",
            target=target,
            new_status="FINISHED",
            title="Bitcoin & Crypto Address Intelligence Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
