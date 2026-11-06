import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.social_x.tools.tweet_harvester.engine import run_engine as run_tweet_harvester
from services.social_x.tools.handle_analyzer.engine import run_engine as run_handle_analyzer
from services.social_x.tools.sentiment_tracker.engine import run_engine as run_sentiment_tracker

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['tweet_harvester', 'handle_analyzer', 'sentiment_tracker']
    
    add_log("X (Twitter) Scraping & Recon", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="X (Twitter) Scraping & Recon",
        status="PROCESSING",
        title="X (Twitter) Scraping & Recon Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/social-x"
    )

    findings = []
    try:
        if "tweet_harvester" in tools:
            add_log("X (Twitter) Scraping & Recon", "Launching sub-engine: Tweet Harvester on " + target, "info")
            findings.extend(run_tweet_harvester(target, {"profile": profile}))
        if "handle_analyzer" in tools:
            add_log("X (Twitter) Scraping & Recon", "Launching sub-engine: Handle Analyzer on " + target, "info")
            findings.extend(run_handle_analyzer(target, {"profile": profile}))
        if "sentiment_tracker" in tools:
            add_log("X (Twitter) Scraping & Recon", "Launching sub-engine: Sentiment & Frequency Tracker on " + target, "info")
            findings.extend(run_sentiment_tracker(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="X (Twitter) Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="X (Twitter) Scraping & Recon Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("X (Twitter) Scraping & Recon", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("X (Twitter) Scraping & Recon", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="X (Twitter) Scraping & Recon",
            target=target,
            new_status="FINISHED",
            title="X (Twitter) Scraping & Recon Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
