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
        "version": "v1.4.0",
        "codename": "Multi-Platform Social Expansion & System Transparency",
        "date": "2026-11-12",
        "is_latest": True,
        "badge": "LATEST STABLE",
        "badge_color": "#10b981",
        "summary": "Full integration of native X / Twitter Flash Reconnaissance, dual-tier Pro Mode clusters, responsive two-column workspace overhaul across all intelligence modules, professional SVG vector iconography across the dashboard, and this dedicated Changelog Hub.",
        "user_features": [
            {
                "icon": "🐦",
                "title": "X / Twitter Flash Reconnaissance Mode",
                "category": "Social Media Intelligence",
                "desc": "Inspect public X / Twitter profiles, user bios, join dates, follower metrics, and recent timeline tweets without external redirects. Full post metrics include Likes, Retweets, Replies, and Impression Views."
            },
            {
                "icon": "📸",
                "title": "Inline Media Gallery & Video Previews",
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
                "title": "Dedicated System Changelog & Versioning Hub",
                "category": "Core Platform",
                "desc": "Added an interactive release history portal at /changelog and persistent header/sidebar indicators tracking platform upgrades and intelligence capabilities."
            },
            {
                "icon": "📐",
                "title": "Two-Column Sticky Workspace Redesign",
                "category": "UI & Ergonomics",
                "desc": "Eliminated central scrolling constraints across Username, Domain, Email, and Social Media modules by docking capability guides into persistent, sticky right-side sidebars."
            },
            {
                "icon": "🎨",
                "title": "Professional SVG Vector Iconography",
                "category": "UI & Ergonomics",
                "desc": "Modernized the entire Mission Control Dashboard, replacing informal emojis with clean, high-precision vector SVG badges and operational status indicators."
            }
        ],
        "technical_details": [
            "Implemented asynchronous SQLite credential vault with automatic account pool rotation and proxy cycling.",
            "Created services/social_media_intelligence/backend/twitter_worker.py handling async task scheduling.",
            "Implemented direct query pipelines against user profile endpoints and timeline feeds.",
            "Added graceful session handling for user-supplied session cookies (auth_token and ct0) with clear fallback error guidance.",
            "Added API endpoints: POST /api/social_media_intelligence/twitter/run, GET /twitter/status, and GET /twitter/download.",
            "Integrated automatic multi-format report exports (.json, .md, .csv) into services/social_media_intelligence/reports/."
        ],
        "commit_refs": ["adcd376", "725c384", "7db3952"],
        "metrics": {"modules_active": 5, "engines_connected": 6, "registries": "3,124+"}
    },
    {
        "version": "v1.3.0",
        "codename": "Dual-Engine Email Intelligence & Identity Pivoting",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#6366f1",
        "summary": "Completed the dual-engine Email Intelligence suite featuring 26-provider Mailbox Discovery alongside 124-registry Reverse Account Footprinting with seamless 1-click cross-module pivoting.",
        "user_features": [
            {
                "icon": "📫",
                "title": "Mailbox Discovery by Handle",
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
            "Integrated native email reconnaissance modules into OASIS backend.",
            "Built high-concurrency async nursery worker (engine_worker.py) querying 124 platform registries concurrently in 5-8 seconds.",
            "Added asynchronous MX record resolution and passive handshake validation in mailbox_worker.py.",
            "Generated comprehensive dossiers (email_{target}.json, .md, .csv) under services/email_intelligence/reports/."
        ],
        "commit_refs": ["b4f4d7c", "53dce08"],
        "metrics": {"modules_active": 5, "engines_connected": 5, "registries": "124+"}
    },
    {
        "version": "v1.2.0",
        "codename": "High-Velocity Flash Engines & Ergonomic Workspace Redesign",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#0ea5e9",
        "summary": "Introduced the native Instagram Flash Mode engine, passive non-intrusive email triage (-NP mode), and the initial two-column sticky sidebar redesign to declutter central workspaces.",
        "user_features": [
            {
                "icon": "📸",
                "title": "Instagram Flash Mode (Native In-App Engine)",
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
            "Replaced single-column viewports with responsive CSS Grid layouts (.email-workspace-layout, .username-workspace-layout, .ig-flash-layout).",
            "Implemented internal headless browser automation for dynamic client-side rendered DOM harvesting.",
            "Cleaned up syntax warnings and normalized -webkit-line-clamp standard properties across all modern browsers."
        ],
        "commit_refs": ["ae5dded", "3ba35c3", "e797ac3", "5a1f3ff", "9cd7a3d"],
        "metrics": {"modules_active": 4, "engines_connected": 4, "registries": "120+"}
    },
    {
        "version": "v1.1.0",
        "codename": "Web Surface Analysis & Forensic Evidence Dossiers",
        "date": "2026-11-11",
        "is_latest": False,
        "badge": "STABLE",
        "badge_color": "#8b5cf6",
        "summary": "Introduced Domain & Website Intelligence, standardized multi-format forensic evidence exports (Markdown, JSON, CSV), dynamic real-time progress bars, and strict enterprise brand isolation.",
        "user_features": [
            {
                "icon": "🌐",
                "title": "Domain & Website Intelligence Module",
                "category": "Surface Intelligence",
                "desc": "Deep web surface analysis crawling DNS records (A, MX, NS, TXT), WHOIS registrar records, SSL certificates, external endpoints, and hidden URL parameters."
            },
            {
                "icon": "💾",
                "title": "Multi-Format Evidence Dossiers",
                "category": "Forensic Archival",
                "desc": "1-click forensic archival providing Incident Markdown (.md), Structured Data (.json), and Tabular Spreadsheets (.csv) across all intelligence modules."
            },
            {
                "icon": "🛡️",
                "title": "Strict OASIS Enterprise Brand Isolation",
                "category": "Enterprise Compliance",
                "desc": "Standardized all internal engines and telemetry indicators under pure OASIS branding, removing internal tool leakages from user-facing screens."
            },
            {
                "icon": "⏱️",
                "title": "Dynamic Multi-Stage Progress Telemetry",
                "category": "Live Telemetry",
                "desc": "Real-time animated progress bars with live elapsed timers, percentage indicators, and platform-by-platform audit feedback replacing static spinners."
            },
            {
                "icon": "🚀",
                "title": "Interactive Server Control Daemon (oasis.sh)",
                "category": "Platform Operations",
                "desc": "Interactive shell control tool featuring dynamic port prompts, automated logging, and graceful background PID management."
            }
        ],
        "technical_details": [
            "Integrated high-speed asynchronous web crawler with URL parameter extraction and regex parsers.",
            "Standardized report compilers in service.py with filesystem write sanitation and automatic report directory bootstrapping.",
            "Built unified progress polling callbacks between long-running workers and REST API endpoints.",
            "Added comprehensive .gitignore untracking Python bytecode, virtual environments, and temporary scan output."
        ],
        "commit_refs": ["c6ccabe", "82b7bdb", "9d0b125", "0b4fe49", "e1f6eb8", "b9b38d3", "25e078c", "fb03210", "d1de006", "13738a0", "c90eeb1", "57c0c20"],
        "metrics": {"modules_active": 4, "engines_connected": 3, "registries": "3,000+"}
    },
    {
        "version": "v1.0.0",
        "codename": "OASIS Structural Overhaul & Navigation Shell (Version 1 Genesis)",
        "date": "2026-11-10",
        "is_latest": False,
        "badge": "MILESTONE",
        "badge_color": "#ea580c",
        "summary": "Major architectural overhaul by Oushnik Bhaduri consolidating 250+ loose legacy prototype files into a standardized, modern microservice suite with unified tactical navigation.",
        "user_features": [
            {
                "icon": "🏛️",
                "title": "OASIS Structural Overhaul (Version 1 Genesis)",
                "category": "Core Platform",
                "desc": "Comprehensive restructuring by Oushnik Bhaduri consolidating loose prototype files into an enterprise-grade modular architecture."
            },
            {
                "icon": "🧭",
                "title": "Unified Tactical Navigation Sidebar",
                "category": "Core Platform",
                "desc": "Introduced the permanent tactical left-side navigation sidebar, establishing unified access across Mission Briefing, Target Vault, and Intelligence Modules."
            },
            {
                "icon": "👤",
                "title": "Username & Identity Intelligence",
                "category": "Username Intelligence",
                "desc": "Multi-platform username reconnaissance surveying 3,000+ public registries, code repositories, forums, and developer networks without API keys."
            },
            {
                "icon": "🌓",
                "title": "Tactical Dark / Light Theme System",
                "category": "UI & Ergonomics",
                "desc": "Instant theme toggling between High-Contrast Dark Operations mode and Crisp Light mode with persistent state storage."
            }
        ],
        "technical_details": [
            "FastAPI asynchronous microservice routing architecture with Jinja2 templating.",
            "Comfortable Warm Ember (#f97316) and Slate (#0f172a) design system with responsive CSS custom properties.",
            "Background task execution hooks and process registry (process_manager.py).",
            "Consolidated 250+ loose legacy files into centralized services directory."
        ],
        "commit_refs": ["eeace8f", "199469b"],
        "metrics": {"modules_active": 1, "engines_connected": 1, "registries": "3,000+"}
    },
    {
        "version": "v0.1.0",
        "codename": "Initial Architecture Prototype (Version 0)",
        "date": "2026-11-06",
        "is_latest": False,
        "badge": "PROTOTYPE",
        "badge_color": "#64748b",
        "summary": "Foundational initial commit by Atig Singh establishing the preliminary repository scaffold for the OSINT aggregation system incubated at Ramakrishna Mission Vidyamandira.",
        "user_features": [
            {
                "icon": "🌱",
                "title": "Initial Platform Prototype",
                "category": "Core Platform",
                "desc": "Initial platform codebase by Atig Singh establishing the directory hierarchy and foundational concept incubated at Ramakrishna Mission Vidyamandira."
            },
            {
                "icon": "📁",
                "title": "Initial Reconnaissance Scaffolds",
                "category": "Core Platform",
                "desc": "Early prototype drafts and folder structures for multi-module intelligence gathering."
            }
        ],
        "technical_details": [
            "Initial repository files, requirements specification, and directory hierarchy.",
            "Prototype draft implementations prior to architectural consolidation."
        ],
        "commit_refs": ["bfb942c"],
        "metrics": {"modules_active": 0, "engines_connected": 0, "registries": "0"}
    }
]

def get_all_releases() -> List[Dict[str, Any]]:
    """Returns the full list of semantic version releases."""
    return RELEASES_DATA

def get_latest_version() -> str:
    """Returns the latest version string."""
    if RELEASES_DATA:
        return RELEASES_DATA[0]["version"]
    return "v1.4.0"

def get_changelog_markdown() -> str:
    """Reads and returns the raw CHANGELOG.md content."""
    if CHANGELOG_MD_PATH.exists():
        try:
            return CHANGELOG_MD_PATH.read_text(encoding="utf-8")
        except Exception:
            pass
    return "# OASIS Changelog\nNo markdown changelog found."
