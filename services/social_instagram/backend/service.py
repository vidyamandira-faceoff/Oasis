import time
import threading
from typing import Dict, List, Any
from core.logger import add_log
from core.notifications import add_recon_notification, update_tool_notification

from services.social_instagram.tools.profile_scraper.engine import run_engine as run_profile_scraper
from services.social_instagram.tools.relationship_analyzer.engine import run_engine as run_relationship_analyzer
from services.social_instagram.tools.media_harvester.engine import run_engine as run_media_harvester

_CACHED_FINDINGS: Dict[str, List[Dict[str, Any]]] = {}

def execute_recon_task(target: str, tools: List[str] = None, profile: str = "deep") -> List[Dict[str, Any]]:
    if not tools:
        tools = ['profile_scraper', 'relationship_analyzer', 'media_harvester']
    
    add_log("Instagram Intelligence & Scraping", f"Starting background multi-engine recon on {target}", "info")
    notif = add_recon_notification(
        tool="Instagram Intelligence & Scraping",
        status="PROCESSING",
        title="Instagram Intelligence & Scraping Query Initiated",
        details=f"Engines running for target: {target}",
        target=target,
        action_url="/services/social-instagram"
    )

    findings = []
    try:
        if "profile_scraper" in tools:
            add_log("Instagram Intelligence & Scraping", "Launching sub-engine: Profile Scraper on " + target, "info")
            findings.extend(run_profile_scraper(target, {"profile": profile}))
        if "relationship_analyzer" in tools:
            add_log("Instagram Intelligence & Scraping", "Launching sub-engine: Relationship Analyzer on " + target, "info")
            findings.extend(run_relationship_analyzer(target, {"profile": profile}))
        if "media_harvester" in tools:
            add_log("Instagram Intelligence & Scraping", "Launching sub-engine: Media Harvester on " + target, "info")
            findings.extend(run_media_harvester(target, {"profile": profile}))
        
        _CACHED_FINDINGS[target] = findings
        update_tool_notification(
            tool="Instagram Intelligence & Scraping",
            target=target,
            new_status="FINISHED",
            title="Instagram Intelligence & Scraping Completed",
            details=f"Successfully extracted {len(findings)} intelligence entities for {target}.",
            metrics=f"{len(findings)} Entities Captured"
        )
        add_log("Instagram Intelligence & Scraping", f"Finished background execution for {target}: {len(findings)} entities captured.", "success")
    except Exception as e:
        add_log("Instagram Intelligence & Scraping", f"Error during execution: {e}", "error")
        update_tool_notification(
            tool="Instagram Intelligence & Scraping",
            target=target,
            new_status="FINISHED",
            title="Instagram Intelligence & Scraping Error",
            details=str(e)
        )

    return findings

def get_latest_findings(target: str = None) -> List[Dict[str, Any]]:
    if target and target in _CACHED_FINDINGS:
        return _CACHED_FINDINGS[target]
    if _CACHED_FINDINGS:
        return list(_CACHED_FINDINGS.values())[-1]
    return []
