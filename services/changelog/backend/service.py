"""
OASIS Changelog Service
Manages Semantic Versioning, Release Metadata, and Changelog Presentation.
"""

from typing import List, Dict, Any
from pathlib import Path
from core.config import BASE_DIR

CHANGELOG_MD_PATH = BASE_DIR / "CHANGELOG.md"

# Reusable SVG Icons for Release Feature Cards
SVG_TWITTER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l11.733 16h4.267l-11.733 -16z"/><path d="M4 20l6.768 -6.768m2.46 -2.46l6.772 -6.772"/></svg>'
SVG_IMAGE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'
SVG_SEARCH = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
SVG_ZAP = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
SVG_SCROLL = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><line x1="1.05" y1="12" x2="7" y2="12"/><line x1="17.01" y1="12" x2="22.96" y2="12"/></svg>'
SVG_LAYOUT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="15" y1="3" x2="15" y2="21"/></svg>'
SVG_VECTOR = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
SVG_MAIL = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>'
SVG_PIVOT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>'
SVG_LOCK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
SVG_BATCH = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
SVG_INSTAGRAM = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>'
SVG_COMMENTS = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
SVG_SHIELD = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_DOSSIER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>'
SVG_GLOBE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
SVG_SPEED = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>'
SVG_SERVER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>'
SVG_USER = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
SVG_THEME = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/></svg>'
SVG_SCAFFOLD = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>'
SVG_PHONE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
SVG_LINKEDIN = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>'

RELEASES_DATA: List[Dict[str, Any]] = [
    {
        "version": "v1.5.0",
        "codename": "LinkedIn Workforce Intelligence & Advanced Social Reconnaissance",
        "date": "2026-11-13",
        "is_latest": True,
        "badge": "LATEST STABLE",
        "badge_color": "#10b981",
        "summary": "Integration of zero-credential LinkedIn Flash Workforce Reconnaissance, algorithmic corporate email synthesis, advanced X/Twitter multi-scope search & metric filters, universal UI alignment, and complete emoji purge.",
        "user_features": [
            {
                "icon": SVG_LINKEDIN,
                "title": "LinkedIn Flash Workforce Reconnaissance",
                "category": "Social Media Intelligence",
                "desc": "Discover verified corporate employee directories, professional roles, and LinkedIn profile URLs without account credentials using non-intrusive public indexation."
            },
            {
                "icon": SVG_MAIL,
                "title": "Algorithmic Corporate Email Synthesis",
                "category": "Social Media Intelligence",
                "desc": "Automatically synthesize probable corporate email addresses ({first}.{last}@domain, {f}{last}@domain) from discovered employee names with domain auto-detection and 1-click clipboard copy."
            },
            {
                "icon": SVG_TWITTER,
                "title": "Advanced X / Twitter Intelligence & Filtering",
                "category": "Social Media Intelligence",
                "desc": "Added granular feed scopes (User Profile, Tweets & Replies, Media Only, Search, and Direct Tweet Threads) and advanced query filters (Min Likes, Min Retweets, Since/Until dates, Language, Media-only)."
            },
            {
                "icon": SVG_ZAP,
                "title": "Full Dual-Tier Mode Switcher for All Platforms",
                "category": "Platform Architecture",
                "desc": "Unified Flash Mode vs Pro Mode architecture across all three major platforms: Instagram, Twitter, and LinkedIn, with zero UI disruption."
            },
            {
                "icon": SVG_PIVOT,
                "title": "1-Click Cross-Platform Intelligence Pivots",
                "category": "Investigation Workflow",
                "desc": "Pivot instantly from discovered corporate personnel into Email Intelligence to verify active inboxes or into Username Intelligence to uncover external online handles."
            },
            {
                "icon": SVG_LAYOUT,
                "title": "UI Ergonomic Alignment & Button Fixes",
                "category": "UI & Ergonomics",
                "desc": "Fixed input grid button overflow in Username Intelligence and restored Social Media Mode Switcher cards into a responsive two-column grid on desktop."
            },
            {
                "icon": SVG_VECTOR,
                "title": "Platform-Wide Emoji Purge & Vector Icons",
                "category": "UI & Ergonomics",
                "desc": "Replaced remaining informal emoji icons across all templates with sharp, responsive SVG vectors matching the platform palette."
            },
            {
                "icon": SVG_SHIELD,
                "title": "Retirement of Redundant Telemetry & Vault Views",
                "category": "Core Platform",
                "desc": "Decommissioned legacy Live Telemetry and Target Vault views, replacing them with focused System Changelog navigation and 302 redirects."
            }
        ],
        "technical_details": [
            "Engineered services/social_media_intelligence/backend/linkedin_worker.py utilizing public search indexation engines (Yahoo, Bing, Google).",
            "Implemented multi-variable corporate email synthesis supporting {first}, {last}, {f}, {l}, and {domain} template strings.",
            "Added API endpoints: POST /api/social_media_intelligence/linkedin/run, GET /linkedin/status, and GET /linkedin/download.",
            "Extended Twitter worker and router with advanced filter parameters: min_likes, min_retweets, since_date, until_date, lang, media_only, links_only.",
            "Replaced input-grid 5-column layout with 2-row ergonomic flex design in recon_username.html.",
            "Decommissioned /terminal and /vault routes in server.py and navigation in base.html.",
            "Automated multi-format forensic dossiers (.json, .md, .csv) for corporate workforce discoveries."
        ],
        "commit_refs": ["6888898", "HEAD"],
        "metrics": {"modules_active": 5, "engines_connected": 7, "registries": "3,124+"}
    },
    {
        "version": "v1.4.0",
        "codename": "Multi-Platform Social Expansion & System Transparency",
        "date": "2026-11-12",
        "is_latest": False,
        "badge": "STABLE RELEASE",
        "badge_color": "#64748b",
        "summary": "Full integration of native X / Twitter Flash Reconnaissance, dual-tier Pro Mode clusters, responsive two-column workspace overhaul across all intelligence modules, professional SVG vector iconography across the dashboard, and this dedicated Changelog Hub.",
        "user_features": [
            {
                "icon": SVG_TWITTER,
                "title": "X / Twitter Flash Reconnaissance Mode",
                "category": "Social Media Intelligence",
                "desc": "Inspect public X / Twitter profiles, user bios, join dates, follower metrics, and recent timeline tweets without external redirects. Full post metrics include Likes, Retweets, Replies, and Impression Views."
            },
            {
                "icon": SVG_IMAGE,
                "title": "Inline Media Gallery & Video Previews",
                "category": "Social Media Intelligence",
                "desc": "High-resolution photo and media previews extracted directly from tweet payloads, displayed in an interactive gallery with instant CDN links."
            },
            {
                "icon": SVG_SEARCH,
                "title": "Live Keyword & Hashtag Velocity Tracking",
                "category": "Social Media Intelligence",
                "desc": "Run real-time keyword queries and track hashtag velocity (#osint, @target) across Twitter with source client auditing (Web, iPhone, Android, API)."
            },
            {
                "icon": SVG_ZAP,
                "title": "Dual-Tier Mode Switcher (Flash vs Pro)",
                "category": "Platform Architecture",
                "desc": "Unified mode selection across Instagram and Twitter: switch between instant zero-latency internal Flash Mode and dedicated high-capacity Pro scraping clusters."
            },
            {
                "icon": SVG_SCROLL,
                "title": "Dedicated System Changelog & Versioning Hub",
                "category": "Core Platform",
                "desc": "Added an interactive release history portal at /changelog and persistent header/sidebar indicators tracking platform upgrades and intelligence capabilities."
            },
            {
                "icon": SVG_LAYOUT,
                "title": "Two-Column Sticky Workspace Redesign",
                "category": "UI & Ergonomics",
                "desc": "Eliminated central scrolling constraints across Username, Domain, Email, and Social Media modules by docking capability guides into persistent, sticky right-side sidebars."
            },
            {
                "icon": SVG_VECTOR,
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
                "icon": SVG_MAIL,
                "title": "Mailbox Discovery by Handle",
                "category": "Email Intelligence",
                "desc": "Given an alias or handle, dynamically enumerates and checks active mailboxes across 26+ major email providers including Gmail, ProtonMail, Yahoo, Outlook, and iCloud."
            },
            {
                "icon": SVG_PIVOT,
                "title": "1-Click Cross-Module Identity Pivoting",
                "category": "Identity Correlation",
                "desc": "Discovered email addresses can be forwarded directly into the Reverse Account Footprint engine with one click to harvest linked social and developer accounts."
            },
            {
                "icon": SVG_LOCK,
                "title": "Masked Credential Leakage Harvester",
                "category": "Email Intelligence",
                "desc": "Passive extraction of partially obfuscated phone numbers (+1 *****42) and secondary recovery email domains revealed by authentication endpoints without contacting targets."
            },
            {
                "icon": SVG_BATCH,
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
                "icon": SVG_INSTAGRAM,
                "title": "Instagram Flash Mode (Native In-App Engine)",
                "category": "Social Media Intelligence",
                "desc": "In-app reconnaissance on target handles, bio metadata, follower counts, and recent media thumbnails with automated offline media ZIP packaging."
            },
            {
                "icon": SVG_COMMENTS,
                "title": "Per-Post Deep Comments Extraction",
                "category": "Social Media Intelligence",
                "desc": "Harvests author handles, comment strings, and timestamps directly from post permalinks into an interactive drawer."
            },
            {
                "icon": SVG_SHIELD,
                "title": "Passive Non-Intrusive Email Recon (-NP Mode)",
                "category": "Email Intelligence",
                "desc": "Safe enumeration mode that validates registered accounts while completely suppressing password reset triggers or target notifications."
            },
            {
                "icon": SVG_SEARCH,
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
                "icon": SVG_GLOBE,
                "title": "Domain & Website Intelligence Module",
                "category": "Surface Intelligence",
                "desc": "Deep web surface analysis crawling DNS records (A, MX, NS, TXT), WHOIS registrar records, SSL certificates, external endpoints, and hidden URL parameters."
            },
            {
                "icon": SVG_DOSSIER,
                "title": "Multi-Format Evidence Dossiers",
                "category": "Forensic Archival",
                "desc": "1-click forensic archival providing Incident Markdown (.md), Structured Data (.json), and Tabular Spreadsheets (.csv) across all intelligence modules."
            },
            {
                "icon": SVG_SHIELD,
                "title": "Strict OASIS Enterprise Brand Isolation",
                "category": "Enterprise Compliance",
                "desc": "Standardized all internal engines and telemetry indicators under pure OASIS branding, removing internal tool leakages from user-facing screens."
            },
            {
                "icon": SVG_SPEED,
                "title": "Dynamic Multi-Stage Progress Telemetry",
                "category": "Live Telemetry",
                "desc": "Real-time animated progress bars with live elapsed timers, percentage indicators, and platform-by-platform audit feedback replacing static spinners."
            },
            {
                "icon": SVG_SERVER,
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
                "icon": SVG_SCAFFOLD,
                "title": "OASIS Structural Overhaul (Version 1 Genesis)",
                "category": "Core Platform",
                "desc": "Comprehensive restructuring by Oushnik Bhaduri consolidating loose prototype files into an enterprise-grade modular architecture."
            },
            {
                "icon": SVG_LAYOUT,
                "title": "Unified Tactical Navigation Sidebar",
                "category": "Core Platform",
                "desc": "Introduced the permanent tactical left-side navigation sidebar, establishing unified access across Mission Briefing, Target Vault, and Intelligence Modules."
            },
            {
                "icon": SVG_USER,
                "title": "Username & Identity Intelligence",
                "category": "Username Intelligence",
                "desc": "Multi-platform username reconnaissance surveying 3,000+ public registries, code repositories, forums, and developer networks without API keys."
            },
            {
                "icon": SVG_THEME,
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
                "icon": SVG_SCAFFOLD,
                "title": "Initial Platform Prototype",
                "category": "Core Platform",
                "desc": "Initial platform codebase by Atig Singh establishing the directory hierarchy and foundational concept incubated at Ramakrishna Mission Vidyamandira."
            },
            {
                "icon": SVG_BATCH,
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
