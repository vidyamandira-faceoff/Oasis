"""
OASIS Changelog Service
Manages Semantic Versioning, Release Metadata, and Changelog Presentation.
"""

from typing import List, Dict, Any
from pathlib import Path
from core.config import BASE_DIR

CHANGELOG_MD_PATH = BASE_DIR / "CHANGELOG.md"

RELEASES_DATA: List[Dict[str, Any]] = [
    {
        "version": "v0.6.0",
        "codename": "Multi-Platform Social Expansion & System Transparency",
        "date": "2026-11-12",
        "is_latest": True,
        "badge": "LATEST STABLE",
        "badge_color": "#10b981",
        "summary": "Full integration of native X / Twitter Flash Reconnaissance, dual-tier Pro Mode clusters, responsive two-column workspace overhaul across all intelligence modules, and the release of this dedicated Changelog Hub.",
        "user_features": [
            {
                "icon": "🐦",
                "title": "X / Twitter Flash Reconnaissance Mode",
                "category": "Social Media Intelligence",
                "desc": "Inspect public X / Twitter profiles, user bios, join dates, follower metrics, and recent timeline tweets without external redirects. Full post metrics include Likes, Retweets, Replies, and Impression Views."
            },
            {
                "icon": "📸",
                "title": "Inline Media Grid & Video Previews",
                "category": "Social Media Intelligence",
                "desc": "High-resolution photo and media previews extracted directly from tweet payloads, displayed in an interactive gallery with instant CDN links."
            },
            {
                "icon": "🔍",
                "title": "Live Keyword & Hashtag Velocity Tracking",
                "category": "Social Media Intelligence",
                "desc": "Run real-time keyword queries and track hashtag velocity (#osint, @target) across Twitter with source client auditing (Web, iPhone, Android, API)."
            },
            {
                "icon": "⚡",
                "title": "Dual-Tier Mode Switcher (Flash vs Pro)",
                "category": "Platform Architecture",
                "desc": "Unified mode selection across Instagram and Twitter: switch between instant zero-latency internal Flash Mode and dedicated high-capacity Pro scraping clusters."
            },
            {
                "icon": "📜",
                "title": "Dedicated System Changelog & Versioning Portal",
                "category": "Core Platform",
                "desc": "Added an interactive release history portal at /changelog and persistent header/sidebar indicators tracking platform upgrades, tool integrations, and forensic capabilities."
            },
            {
                "icon": "📐",
                "title": "Two-Column Sticky Workspace Redesign",
                "category": "UI & Ergonomics",
                "desc": "Eliminated central scrolling constraints across Username, Domain, Email, and Social Media modules by docking capability guides into persistent, sticky right-side sidebars."
            }
        ],
        "technical_details": [
            "Bound twscrape_OSINT into virtual environment with aiosqlite, curl-cffi, and loguru.",
            "Created services/social_media_intelligence/backend/twitter_worker.py with SQLite account pool management (twscrape_accounts.db).",
            "Implemented direct bindings against Twitter GraphQL endpoints: OP_UserByScreenName, OP_UserTweets, OP_SearchTimeline.",
            "Added graceful session handling for user-supplied auth_token and ct0 session cookies with clear fallback alerts.",
            "Added API endpoints: POST /api/social_media_intelligence/twitter/run, GET /twitter/status, and GET /twitter/download.",
            "Integrated automatic multi-format report exports (.json, .md, .csv) into services/social_media_intelligence/reports/."
        ],
        "commit_refs": ["adcd376"],
        "metrics": {"modules_active": 5, "engines_connected": 6, "registries": "3,124+"}
    },
    {
        "version": "v0.5.0",
        "codename": "Dual-Engine Email Intelligence & Identity Pivoting",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#6366f1",
        "summary": "Completed the dual-engine Email Intelligence suite featuring 26-provider Mailbox Discovery (Mailcat) alongside 124-registry Reverse Account Footprinting (Holehe) with seamless 1-click cross-module pivoting.",
        "user_features": [
            {
                "icon": "📫",
                "title": "Mailbox Discovery by Handle (Mailcat Engine)",
                "category": "Email Intelligence",
                "desc": "Given an alias or handle, dynamically enumerates and checks active mailboxes across 26+ major email providers including Gmail, ProtonMail, Yahoo, Outlook, and iCloud."
            },
            {
                "icon": "🔄",
                "title": "1-Click Cross-Module Identity Pivoting",
                "category": "Identity Correlation",
                "desc": "Discovered email addresses can be forwarded directly into the Reverse Account Footprint engine with one click to harvest linked social and developer accounts."
            },
            {
                "icon": "🔐",
                "title": "Masked Credential Leakage Harvester",
                "category": "Email Intelligence",
                "desc": "Passive extraction of partially obfuscated phone numbers (+1 *****42) and secondary recovery email domains revealed by authentication endpoints without contacting targets."
            },
            {
                "icon": "📑",
                "title": "Single & Batch Email Reconnaissance",
                "category": "Email Intelligence",
                "desc": "Flexible operational modes: survey a single target or paste multi-line email lists to scan entire corporate domains or threat actor groups in parallel."
            }
        ],
        "technical_details": [
            "Linked holehe_OSINT and mailcat_OSINT into OASIS backend architecture.",
            "Built Trio asynchronous nursery worker (engine_worker.py) auditing 124 platform registries concurrently in 5-8 seconds.",
            "Integrated async DNS MX verification and direct passive SMTP handshake checking in mailbox_worker.py.",
            "Added standardized dossier generation (.json, .md, .csv) under services/email_intelligence/reports/."
        ],
        "commit_refs": ["b4f4d7c", "53dce08"],
        "metrics": {"modules_active": 5, "engines_connected": 5, "registries": "124+"}
    },
    {
        "version": "v0.4.0",
        "codename": "High-Velocity Flash Engines & Ergonomic Workspace",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#0ea5e9",
        "summary": "Introduced the native Instagram Flash Mode engine, passive non-intrusive email triage (-NP mode), and the initial two-column sticky sidebar redesign to declutter central workspaces.",
        "user_features": [
            {
                "icon": "📸",
                "title": "Instagram Flash Mode (Native Chromium)",
                "category": "Social Media Intelligence",
                "desc": "In-app reconnaissance on target handles, bio metadata, follower counts, and recent media thumbnails with automated offline media ZIP packaging."
            },
            {
                "icon": "💬",
                "title": "Per-Post Deep Comments Extraction",
                "category": "Social Media Intelligence",
                "desc": "Harvests author handles, comment strings, and timestamps directly from post permalinks into an interactive drawer."
            },
            {
                "icon": "🛡️",
                "title": "Passive Non-Intrusive Email Recon (-NP Mode)",
                "category": "Email Intelligence",
                "desc": "Safe enumeration mode that validates registered accounts while completely suppressing password reset triggers or target notifications."
            },
            {
                "icon": "📊",
                "title": "Audit Survey Registry Grid",
                "category": "Email Intelligence",
                "desc": "Categorizes platform scan results into Confirmed Registrations, Free Targets, and Platform Errors with instant search filtering."
            }
        ],
        "technical_details": [
            "Refactored single-column viewports into two-column CSS Grid layouts (.email-workspace-layout, .username-workspace-layout, .ig-flash-layout).",
            "Integrated Pyppeteer headless Chromium automation for dynamic Instagram client-side DOM scraping.",
            "Fixed CSS vendor prefixes and multi-line clamps across modern browsers."
        ],
        "commit_refs": ["ae5dded", "3ba35c3", "e797ac3", "5a1f3ff", "9cd7a3d"],
        "metrics": {"modules_active": 4, "engines_connected": 4, "registries": "120+"}
    },
    {
        "version": "v0.3.0",
        "codename": "Multi-Format Forensic Archival & Telemetry Feedback",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#8b5cf6",
        "summary": "Added standard multi-format forensic exports (Markdown, JSON, CSV), dynamic real-time progress bars with stage-by-stage feedback, and phone number scraper integration.",
        "user_features": [
            {
                "icon": "💾",
                "title": "Multi-Format Evidence Dossiers",
                "category": "Forensic Archival",
                "desc": "1-click forensic archival providing Incident Markdown (.md), Structured Data (.json), and Tabular Spreadsheets (.csv) across all intelligence modules."
            },
            {
                "icon": "⏱️",
                "title": "Dynamic Multi-Stage Progress Telemetry",
                "category": "Live Telemetry",
                "desc": "Real-time animated progress bars with live elapsed timers, percentage indicators, and platform-by-platform audit feedback replacing static spinners."
            },
            {
                "icon": "📱",
                "title": "Phone Number Intelligence Launchpad",
                "category": "Phone Intelligence",
                "desc": "Direct integration linking to dedicated telecom carrier resolution, regional circle tracking, and line type validation cluster."
            },
            {
                "icon": "🧹",
                "title": "Streamlined Navigation & Header Bars",
                "category": "UI & Ergonomics",
                "desc": "Cleaned up visual clutter, unified status pills, and removed redundant tool icons across all active viewports."
            }
        ],
        "technical_details": [
            "Standardized report compilers in service.py with filesystem write sanitation and automatic report directory bootstrapping.",
            "Added unified progress polling callbacks between long-running workers and REST API endpoints.",
            "Purged legacy mock files and sanitized target records."
        ],
        "commit_refs": ["57c0c20", "c90eeb1", "13738a0", "d1de006", "3e0607b", "984ab0d"],
        "metrics": {"modules_active": 4, "engines_connected": 3, "registries": "3,000+"}
    },
    {
        "version": "v0.2.0",
        "codename": "Surface Analysis & Enterprise Brand Isolation",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#f59e0b",
        "summary": "Introduced Domain & Website Intelligence (Photon integration), complete enterprise brand isolation (purging tool name leaks), and the interactive oasis.sh server daemon.",
        "user_features": [
            {
                "icon": "🌐",
                "title": "Domain & Website Intelligence Module",
                "category": "Surface Intelligence",
                "desc": "Deep web surface analysis crawling DNS records (A, MX, NS, TXT), WHOIS registrar records, SSL certificates, external endpoints, and hidden URL parameters."
            },
            {
                "icon": "🛡️",
                "title": "Strict OASIS Brand Isolation",
                "category": "Enterprise Compliance",
                "desc": "Purged internal third-party engine names from user-facing screens, telemetry, and reports; all capabilities presented under unified OASIS platform branding."
            },
            {
                "icon": "🧭",
                "title": "Revamped Mission Briefing Dashboard",
                "category": "Core Platform",
                "desc": "Redesigned overview dashboard displaying live intelligence module counts, active background processes, and local IST clocks."
            },
            {
                "icon": "🚀",
                "title": "Interactive Server Control Daemon (oasis.sh)",
                "category": "Platform Operations",
                "desc": "Interactive shell control tool featuring dynamic port prompts, automated logging, and graceful background PID management."
            }
        ],
        "technical_details": [
            "Integrated Photon_osint_url web crawler with asynchronous HTTP and URL parameter parsers.",
            "Fixed Python engine sys.path resolution for external tool sandboxes (maigret, photon).",
            "Added comprehensive .gitignore untracking Python bytecode, virtual environments, and temporary scan output."
        ],
        "commit_refs": ["e1f6eb8", "b9b38d3", "25e078c", "fb03210", "c6ccabe", "82b7bdb", "9d0b125", "0b4fe49"],
        "metrics": {"modules_active": 3, "engines_connected": 2, "registries": "3,000+"}
    },
    {
        "version": "v0.1.0",
        "codename": "Platform Genesis & Tactical Operations Shell",
        "date": "2026-11-10",
        "is_latest": False,
        "badge": "FOUNDATION",
        "badge_color": "#64748b",
        "summary": "The initial genesis release of the OSINT Aggregation and Strategic Intelligence System (OASIS), incubated at Ramakrishna Mission Vidyamandira.",
        "user_features": [
            {
                "icon": "🏛️",
                "title": "OASIS Platform Genesis",
                "category": "Core Platform",
                "desc": "Foundational deployment of the intelligence hub incubated at Ramakrishna Mission Vidyamandira."
            },
            {
                "icon": "👤",
                "title": "Username Intelligence Module",
                "category": "Username Intelligence",
                "desc": "Multi-platform username reconnaissance surveying 3,000+ public registries, code repositories, and developer networks without API keys."
            },
            {
                "icon": "🌓",
                "title": "Tactical Dark / Light Theme System",
                "category": "UI & Ergonomics",
                "desc": "Instant theme toggling between High-Contrast Dark Operations mode and Crisp Light mode with persistent state storage."
            },
            {
                "icon": "🧭",
                "title": "Tactical Operations Shell",
                "category": "Core Platform",
                "desc": "Integrated navigation connecting Mission Briefing, Target Vault, Live Telemetry, and active Intelligence Modules."
            }
        ],
        "technical_details": [
            "FastAPI asynchronous microservice routing architecture with Jinja2 templating.",
            "Comfortable Warm Ember and Slate design system with responsive CSS custom properties.",
            "Foundational background task execution hooks and system telemetry status APIs."
        ],
        "commit_refs": ["bfb942c", "eeace8f", "199469b"],
        "metrics": {"modules_active": 1, "engines_connected": 1, "registries": "3,000+"}
    }
]

def get_all_releases() -> List[Dict[str, Any]]:
    """Returns the full list of semantic version releases."""
    return RELEASES_DATA

def get_latest_version() -> str:
    """Returns the latest version string."""
    if RELEASES_DATA:
        return RELEASES_DATA[0]["version"]
    return "v0.6.0"

def get_changelog_markdown() -> str:
    """Reads and returns the raw CHANGELOG.md content."""
    if CHANGELOG_MD_PATH.exists():
        try:
            return CHANGELOG_MD_PATH.read_text(encoding="utf-8")
        except Exception:
            pass
    return "# OASIS Changelog\nNo markdown changelog found."
