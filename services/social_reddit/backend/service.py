import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.social_reddit.tools.subreddit_crawler.engine import run_engine as run_subreddit_crawler
from services.social_reddit.tools.user_dossier.engine import run_engine as run_user_dossier
from services.social_reddit.tools.thread_extractor.engine import run_engine as run_thread_extractor

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['subreddit_crawler', 'user_dossier', 'thread_extractor']
    
    add_log("Reddit Scraping & Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Reddit Scraping & Recon",
        status="PROCESSING",
        title="Reddit Scraping & Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/social-reddit"
    )

    findings = []
    try:
        if "subreddit_crawler" in tools:
            add_log("Reddit Scraping & Recon", "Launching sub-engine: Subreddit Crawler on " + target, "info")
            findings.extend(run_subreddit_crawler(target, {"profile": profile}))
        if "user_dossier" in tools:
            add_log("Reddit Scraping & Recon", "Launching sub-engine: User Dossier Builder on " + target, "info")
            findings.extend(run_user_dossier(target, {"profile": profile}))
        if "thread_extractor" in tools:
            add_log("Reddit Scraping & Recon", "Launching sub-engine: Thread Extractor on " + target, "info")
            findings.extend(run_thread_extractor(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Reddit Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="Reddit Scraping & Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Reddit Scraping & Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Reddit Scraping & Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Reddit Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="Reddit Scraping & Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
