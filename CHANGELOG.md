# OASIS Release Changelog & Version History

All notable changes to the **OASIS** (OSINT Aggregation and Strategic Intelligence System) platform are documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`MAJOR.MINOR.PATCH`):
- **MAJOR**: Structural overhauls, core architecture redesigns, and milestone platform releases.
- **MINOR**: New intelligence modules, native scraping engine integrations, or major capability additions.
- **PATCH**: UI refinements, bug fixes, engine dependency patches, and security improvements.

---

## [v1.5.0] - 2026-11-13
### Codename: LinkedIn Workforce Intelligence & Advanced Social Reconnaissance
*Commit References: `6888898`, `HEAD`*

#### User-Centric Capabilities & Feature Releases
- **LinkedIn Corporate Workforce Flash Mode**:
  - Full in-app corporate personnel discovery across organizations without requiring LinkedIn authentication or credentials.
  - Harvests verified employee full names, job titles, and clickable public profile URLs via multi-engine public indexation.
  - Department and role filtering (Engineering & Dev, Security & OSINT, Leadership & Execs, AI & Research, Product & Design).
  - Algorithmic corporate email synthesis supporting standard naming formats (`{first}.{last}@domain`, `{f}{last}@domain`, `{first}@domain`) with domain auto-detection.
  - 1-click clipboard copy for synthesized corporate email addresses.
  - Interactive workforce findings table with direct cross-engine pivots into Email Intelligence and Username Intelligence.
- **Advanced X / Twitter Intelligence & Filtering**:
  - Expanded feed scopes: User Profile & Tweets, Tweets & Conversation Replies, Media Gallery Only, Keyword & Hashtag Search, and Direct Tweet & Thread extraction.
  - Advanced query filters: Minimum Likes (`min_faves`), Minimum Retweets (`min_retweets`), Date Range boundaries (`since` / `until`), Language selection (`lang:en`, `lang:es`, `lang:ja`, etc.), Media-only flags, and Links-only filtering.
  - Responsive multi-column layout for advanced query parameters.
- **Unified Dual-Tier Architecture for All Platforms**:
  - Completed Flash Mode vs Pro Mode dual-tier design across all three major platforms: Instagram, Twitter, and LinkedIn.
- **UI Ergonomics & Button Overflow Fixes**:
  - Restructured Username Intelligence input grid into an ergonomic two-tier layout, ensuring `Execute Reconnaissance` and `Re-run Fresh Scan` action buttons never overflow card borders.
  - Restored Social Media Intelligence Mode Switcher cards into a responsive two-column grid on desktop, eliminating single-column vertical stacking.
- **Universal Platform-Wide Emoji Purge**:
  - Replaced remaining informal emoji icons across all templates with sharp, responsive SVG vectors matching the platform palette.
- **Decommissioning Legacy Views**:
  - Decommissioned obsolete Live Telemetry and Target Vault views, replacing them with focused System Changelog navigation and automatic 302 redirects.

<details>
<summary>Technical & Architectural Details (Click to Expand)</summary>

- **Workforce Engine**: Created `services/social_media_intelligence/backend/linkedin_worker.py` utilizing public search indexation engines (Yahoo, Bing, Google).
- **Email Synthesizer**: Engineered multi-variable corporate email synthesis supporting `{first}`, `{last}`, `{f}`, `{l}`, and `{domain}` template strings.
- **Microservice Routing**: Added `POST /api/social_media_intelligence/linkedin/run`, `GET /linkedin/status`, and `GET /linkedin/download`.
- **Twitter Engine Extensions**: Extended Twitter worker and router with advanced filter parameters: `min_likes`, `min_retweets`, `since_date`, `until_date`, `lang`, `media_only`, `links_only`.
- **UI Grid Refactoring**: Replaced `input-grid` 5-column layout with 2-row ergonomic flex design in `recon_username.html`.
- **Legacy Route Deprecation**: Decommissioned `/terminal` and `/vault` routes in `server.py` and navigation in `base.html` with graceful HTTP 302 redirects.
- **Forensic Dossiers**: Automated multi-format forensic dossiers (`.json`, `.md`, `.csv`) for corporate workforce discoveries.
</details>

---

## [v1.4.0] - 2026-11-12
### Codename: Multi-Platform Social Expansion & System Transparency
*Commit References: `adcd376`, `725c384`, `7db3952`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **X / Twitter Flash Reconnaissance Mode**:
  - Full in-app reconnaissance on X / Twitter profiles, user bios, join dates, and follower metrics without external redirects.
  - Interactive Tweets Timeline with full engagement metrics: Likes, Retweets, Replies, and Impression Views.
  - Direct tweet media extraction showcasing high-resolution photo and video previews in an inline gallery.
  - Keyword and hashtag discovery (`#osint`, `@target`) with live velocity tracking.
  - Source client auditing (identifying whether tweets were sent from Web, iPhone, Android, or automated APIs).
- **Dual-Tier Social Engine Switcher**:
  - Unified mode switcher between **Flash Mode** (instant internal headless/GraphQL engine) and **Pro Mode** (external high-capacity scraper clusters).
- **Dedicated System Changelog & Versioning Hub**:
  - Live interactive portal at `/changelog` tracking platform updates, newly added capabilities, and intelligence features.
  - Quick-access version badge (`v1.4.0`) in the global navigation header and tactical sidebar.
- **Two-Column Sticky Workspace Across All Modules**:
  - Resolved vertical scrolling constraints by docking capability guides into persistent, sticky right-hand panels across Username, Domain, Email, and Social Media modules.
- **Professional SVG Vector Iconography**:
  - Modernized the entire Mission Control Dashboard, replacing informal emojis with clean, high-precision vector SVG badges and operational indicators.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Engine Architecture**: Implemented asynchronous SQLite credential vault with automatic account pool rotation and proxy cycling.
- **Backend Worker**: Created `services/social_media_intelligence/backend/twitter_worker.py` handling async task scheduling.
- **GraphQL Bindings**: Implemented direct query pipelines against user profile endpoints and timeline feeds.
- **Session Injection**: Added graceful session handling for user-supplied session cookies (`auth_token` and `ct0`) with clear fallback error guidance.
- **Microservice Routing**: Added `POST /api/social_media_intelligence/twitter/run`, `GET /twitter/status`, and `GET /twitter/download`.
- **Forensic Exports**: Automatic compilation of Twitter dossiers into `.json`, `.md`, and `.csv` under `services/social_media_intelligence/reports/`.
</details>

---

## [v1.3.0] - 2026-11-11
### Codename: Dual-Engine Email Intelligence & Identity Pivoting
*Commit References: `b4f4d7c`, `53dce08`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Mailbox Discovery by Handle**:
  - Given an alias or handle, dynamically verifies active email inboxes across 26+ major email providers (Gmail, ProtonMail, Outlook, Yahoo, iCloud, Mail.com, etc.).
- **1-Click Cross-Module Identity Pivot**:
  - Seamlessly pivots discovered mailboxes directly into the Reverse Account Footprint engine with one click, uncovering linked social profiles instantly.
- **Masked Credential Leakage Harvester**:
  - Passive discovery of partially masked phone numbers (e.g. `+1 *****42`) and recovery emails revealed by authentication portals without alerting the target.
- **Single & Batch Reconnaissance Modes**:
  - Analysts can scan a single target email or paste multi-line email lists to survey entire organizations simultaneously.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Engine Architecture**: Integrated native email reconnaissance modules into OASIS backend.
- **Asynchronous Nurseries**: Implemented high-concurrency async nursery worker (`engine_worker.py`) querying 124 platform registries concurrently in 5-8 seconds.
- **DNS & SMTP Verification**: Added asynchronous MX record resolution and passive handshake validation in `mailbox_worker.py`.
- **Standardized Reports**: Generated comprehensive dossiers (`email_{target}.json`, `.md`, `.csv`) in `services/email_intelligence/reports/`.
</details>

---

## [v1.2.0] - 2026-11-11
### Codename: High-Velocity Flash Engines & Ergonomic Workspace Redesign
*Commit References: `ae5dded`, `3ba35c3`, `e797ac3`, `5a1f3ff`, `9cd7a3d`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Two-Column Sticky Ergonomic Workspace**:
  - Relocated bulky feature grids from the center of the screen into sticky right-side capability panels across Username, Domain, and Social Media modules, keeping the main screen scrolling-free.
- **Instagram Flash Mode (Native In-App Engine)**:
  - Zero-latency in-app reconnaissance on Instagram profiles, biographies, follower counts, and recent media thumbnails.
  - Per-post comment mining and one-click offline media ZIP packaging.
- **Passive Non-Intrusive Email Recon (`-NP`)**:
  - Passive detection mode that suppresses password reset triggers, avoiding sending OTPs or security alerts to targets.
- **Audit Survey Grid**:
  - Tabbed breakdown categorized into Confirmed Registrations, Free Targets, and Platform Errors with quick search filtering.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **CSS Layout Architecture**: Replaced single-column layouts with responsive CSS Grid layouts (`.email-workspace-layout`, `.username-workspace-layout`, `.ig-flash-layout`).
- **Headless Browser Integration**: Implemented internal headless browser automation for dynamic client-side rendered DOM harvesting.
- **CSS Bug Fixes**: Cleaned up syntax warnings and normalized `-webkit-line-clamp` standard properties across all modern browsers.
</details>

---

## [v1.1.0] - 2026-11-11
### Codename: Web Surface Analysis & Forensic Evidence Dossiers
*Commit References: `c6ccabe`, `82b7bdb`, `9d0b125`, `0b4fe49`, `e1f6eb8`, `b9b38d3`, `25e078c`, `fb03210`, `d1de006`, `13738a0`, `c90eeb1`, `57c0c20`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Domain & Website Intelligence Module**:
  - Deep web surface analysis crawling DNS records (A, MX, NS, TXT), WHOIS registrar history, SSL certificates, external endpoints, and hidden URL parameters.
- **Multi-Format Forensic Evidence Dossiers**:
  - One-click downloads for Case Dossier Markdown (`.md`), Structured Data (`.json`), and Tabular Spreadsheet (`.csv`) across all active intelligence modules.
- **Strict OASIS Enterprise Brand Isolation**:
  - Standardized all internal engines and telemetry indicators under pure OASIS branding, removing internal tool leakages from user-facing screens.
- **Dynamic Multi-Stage Progress Telemetry**:
  - Real-time animated progress bars with live elapsed timers, percentage indicators, and platform-by-platform audit feeds.
- **Interactive Server Control Daemon (`oasis.sh`)**:
  - Interactive CLI control tool with custom port prompts, graceful shutdowns, and background process monitoring.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Web Surface Engine**: Integrated high-speed asynchronous web crawler with URL parameter extraction and regex parsers.
- **Dossier Standardization**: Implemented unified report compilers in `service.py` with write protection and automatic folder bootstrapping.
- **Process Management**: Fixed Python engine path resolution and created standardized API status polling responses (`status`, `elapsed`, `progress_msg`, `dossier_files`).
- **Repository Hygiene**: Added comprehensive `.gitignore` rules untracking bytecode, virtual environments, and temporary scan outputs.
</details>

---

## [v1.0.0] - 2026-11-10
### Codename: OASIS Structural Overhaul & Navigation Shell (Version 1 Genesis)
*Commit References: `eeace8f`, `199469b`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **OASIS Architecture Overhaul**:
  - Major platform restructuring by Oushnik Bhaduri consolidating 250+ loose legacy prototype files into a clean, modern microservice architecture.
- **Tactical Navigation Sidebar**:
  - Introduced the permanent left-side tactical navigation sidebar (`base.html`), standardizing module access across Core Platform and Intelligence Suites.
- **Username & Identity Intelligence**:
  - Multi-platform username enumeration surveying 3,000+ public registries, code repositories, forums, and creator networks.
- **Tactical Dark/Light Theme Engine**:
  - Instant theme switching between High-Contrast Dark Operations mode and Crisp Light mode with browser persistence.
- **Mission Briefing Dashboard**:
  - Initial unified operations dashboard connecting Target Vault, Live Telemetry, and active Intelligence Modules.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Platform Architecture**: Built on FastAPI asynchronous microservice architecture with Jinja2 server-side rendering.
- **Design System**: Implemented Warm Ember (`#f97316`), Deep Slate (`#0f172a`), and modern responsive card layouts.
- **Process Registry**: Built background task execution manager and process registry (`process_manager.py`).
- **Codebase Consolidation**: Purged unneeded duplicate files and standardized module router conventions.
</details>

---

## [v0.1.0] - 2026-11-06
### Codename: Initial Architecture Prototype (Version 0)
*Commit Reference: `bfb942c`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Initial Platform Prototype**:
  - Foundational initial commit by Atig Singh establishing the preliminary repository scaffold for the OSINT aggregation system incubated at Ramakrishna Mission Vidyamandira.
- **Initial Reconnaissance Scaffolds**:
  - Early directory layout and prototype structures for multi-module intelligence gathering.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Repository Scaffold**: Initial repository files, requirements specification, and directory hierarchy.
- **Prototype Modules**: Early drafts of recon modules prior to architectural consolidation.
</details>
