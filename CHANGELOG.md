# OASIS Release Changelog & Version History

All notable changes to the **OASIS** (OSINT Aggregation and Strategic Intelligence System) platform are documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`MAJOR.MINOR.PATCH`):
- **MAJOR**: Breaking platform architecture changes or milestone redesigns.
- **MINOR**: New intelligence modules, scraping engine integrations, or major capability additions.
- **PATCH**: UI refinements, bug fixes, engine dependency patches, and security improvements.

---

## [v0.6.0] - 2026-11-12
### Codename: Multi-Platform Social Expansion & System Transparency
*Commit References: `adcd376`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **X / Twitter Flash Reconnaissance Mode**:
  - Full in-app reconnaissance on X / Twitter profiles, user bios, join dates, and follower metrics without external redirects.
  - Interactive Tweets Timeline with full engagement metrics: Likes, Retweets, Replies, and Impression Views.
  - Direct tweet media extraction showcasing high-resolution photo and video previews in an inline grid.
  - Keyword and hashtag discovery (`#osint`, `@target`) with live velocity tracking.
  - Source client auditing (identifying whether tweets were sent from Web, iPhone, Android, or automated APIs).
- **Dual-Tier Social Engine Switcher**:
  - Unified mode switcher between **Flash Mode** (instant internal headless/GraphQL engine) and **Pro Mode** (external high-capacity scraper clusters at `http://xintel.rkmvcse.in/` and `http://instagramintel.rkmvcse.in/`).
- **Dedicated System Changelog & Versioning Hub**:
  - Live interactive portal at `/changelog` tracking platform updates, newly integrated OSINT tools, and intelligence features.
  - Quick-access version badge (`v0.6.0`) in the global navigation header and tactical sidebar.
- **Two-Column Sticky Workspace Across All Modules**:
  - Resolved vertical scrolling constraints by docking capability guides into persistent, sticky right-hand panels across Username, Domain, Email, and Social Media modules.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Engine Integration**: Bound `twscrape_OSINT` into the OASIS virtual environment with `aiosqlite`, `curl-cffi`, and `loguru`.
- **Backend Worker**: Created `services/social_media_intelligence/backend/twitter_worker.py` utilizing persistent SQLite account pool (`twscrape_accounts.db`).
- **GraphQL Bindings**: Implemented queries against official Twitter GraphQL endpoints: `OP_UserByScreenName`, `OP_UserTweets`, and `OP_SearchTimeline`.
- **Session Injection**: Added graceful session handling for user-supplied `auth_token` and `ct0` cookies with clean fallback error guidance.
- **Microservice Routing**: Added `POST /api/social_media_intelligence/twitter/run`, `GET /twitter/status`, and `GET /twitter/download`.
- **Forensic Exports**: Automatic compilation of Twitter dossiers into `.json`, `.md`, and `.csv` under `services/social_media_intelligence/reports/`.
</details>

---

## [v0.5.0] - 2026-11-11
### Codename: Dual-Engine Email Intelligence & Identity Pivoting
*Commit References: `b4f4d7c`, `53dce08`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Mailbox Discovery by Handle (Mailcat Integration)**:
  - Given an alias or username, dynamically verifies active email inboxes across 26+ major email providers (Gmail, ProtonMail, Outlook, Yahoo, iCloud, Mail.com, etc.).
- **1-Click Cross-Module Identity Pivot**:
  - Seamlessly pivots discovered mailboxes directly into the Reverse Account Footprint engine with one click, uncovering linked social profiles instantly.
- **Masked Data Harvesting**:
  - Passive discovery of partially masked phone numbers (e.g. `+1 *****42`) and recovery emails revealed by authentication portals without alerting the target.
- **Single & Batch Reconnaissance Modes**:
  - Analysts can scan a single target email or paste multi-line email lists to survey entire organizations simultaneously.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Engine Architecture**: Linked `holehe_OSINT` and `mailcat_OSINT` into OASIS backend.
- **Asynchronous Nurseries**: Implemented Trio async engine worker (`engine_worker.py`) querying 120+ authentication endpoints concurrently in 5-8 seconds.
- **DNS & SMTP Verification**: Added asynchronous MX record resolution and passive handshake validation in `mailbox_worker.py`.
- **Standardized Reports**: Generated comprehensive dossiers (`email_{target}.json`, `.md`, `.csv`) in `services/email_intelligence/reports/`.
</details>

---

## [v0.4.0] - 2026-11-11
### Codename: High-Velocity Flash Engines & Ergonomic Workspace Redesign
*Commit References: `ae5dded`, `3ba35c3`, `e797ac3`, `5a1f3ff`, `9cd7a3d`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Two-Column Sticky Ergonomic Workspace**:
  - Relocated bulky feature grids from the center of the screen into sticky right-side capability panels across Username, Domain, and Social Media modules, keeping the main screen scrolling-free.
- **Instagram Flash Mode (Native Chromium Engine)**:
  - Zero-latency in-app reconnaissance on Instagram profiles, biographies, follower counts, and recent media thumbnails.
  - Per-post comment mining and one-click offline media ZIP packaging.
- **Passive Non-Intrusive Email Recon (`-NP`)**:
  - Passive detection mode that suppresses password reset triggers, avoiding sending OTPs or security alerts to targets.
- **Audit Survey Grid**:
  - Tabbed breakdown categorized into Confirmed Registrations, Free Targets, and Platform Errors with quick search filtering.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **CSS Layout Architecture**: Replaced single-column layouts with responsive CSS Grid layouts (`.email-workspace-layout`, `.username-workspace-layout`, `.ig-flash-layout`).
- **Headless Browser Integration**: Implemented Pyppeteer headless Chromium automation for client-side JavaScript rendering on Instagram profiles.
- **CSS Bug Fixes**: Cleaned up syntax warnings and normalized `-webkit-line-clamp` standard properties.
</details>

---

## [v0.3.0] - 2026-11-11
### Codename: Multi-Format Forensic Archival & Telemetry Feedback
*Commit References: `57c0c20`, `c90eeb1`, `13738a0`, `d1de006`, `3e0607b`, `984ab0d`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Multi-Format Forensic Evidence Dossiers**:
  - One-click downloads for Case Dossier Markdown (`.md`), Structured Data (`.json`), and Tabular Spreadsheet (`.csv`) across all active intelligence modules.
- **Dynamic Multi-Stage Progress Telemetry**:
  - Real-time animated progress bars with live elapsed timers, stage indicators, and platform-by-platform audit feeds.
- **Cleaned Tactical Header Bars**:
  - Streamlined service header banners, removing redundant visual elements and aligning navigation icons.
- **Phone Number Intelligence Launchpad**:
  - Direct integration linking to high-capacity telecom carrier, circle lookup, and line type validation cluster (`https://investigator.rkmvcse.in/`).

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Dossier Standardization**: Implemented unified report compilers in `service.py` with write protection and automatic folder bootstrapping.
- **Worker Polling Protocol**: Standardized API status polling responses (`status`, `elapsed`, `progress_msg`, `dossier_files`).
- **Data Cleanup**: Purged legacy sample reports and normalized platform identifiers.
</details>

---

## [v0.2.0] - 2026-11-11
### Codename: Surface Analysis & Enterprise Brand Isolation
*Commit References: `e1f6eb8`, `b9b38d3`, `25e078c`, `fb03210`, `c6ccabe`, `82b7bdb`, `9d0b125`, `0b4fe49`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **Domain & Website Intelligence Module**:
  - Deep web surface analysis crawling DNS records (A, MX, NS, TXT), WHOIS registrar history, SSL certificates, external endpoints, and hidden URL parameters.
- **Strict OASIS Enterprise Brand Isolation**:
  - Purged internal engine names from user-facing screens and telemetry; all capabilities presented under unified OASIS platform branding.
- **Revamped Mission Briefing Dashboard**:
  - Modernized overview dashboard displaying real-time intelligence telemetry, active modules counter, and local IST system clocks.
- **Interactive Server Control Script (`oasis.sh`)**:
  - Interactive CLI control tool with custom port prompts, graceful shutdowns, and background process monitoring.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Web Surface Engine**: Integrated `Photon_osint_url` web crawler with async requests and regex data extraction.
- **Path Resolution**: Fixed Python engine `sys.path` resolution for external tool sandboxes (`maigret`, `photon`).
- **Repository Hygiene**: Added comprehensive `.gitignore` rules untracking `__pycache__`, virtual environments, and temporary scan output.
</details>

---

## [v0.1.0] - 2026-11-10
### Codename: Platform Genesis & Tactical Operations Shell
*Commit References: `bfb942c`, `eeace8f`, `199469b`*

#### 🌟 User-Centric Capabilities & Feature Releases
- **OASIS Platform Genesis**:
  - Initial platform release of the OSINT Aggregation and Strategic Intelligence System, incubated at Ramakrishna Mission Vidyamandira.
- **Username Intelligence Module**:
  - Multi-platform username enumeration surveying 3,000+ public registries, code repositories, forums, and creator networks.
- **Tactical Dark/Light Theme Engine**:
  - Instant theme switching between High-Contrast Dark Operations mode and Crisp Light mode with browser persistence.
- **Core Operations Shell**:
  - Integrated navigation connecting Mission Briefing, Target Repository, Live Telemetry, and Module registries.

<details>
<summary>⚙️ Technical & Architectural Details (Click to Expand)</summary>

- **Platform Architecture**: Built on FastAPI asynchronous microservice architecture with Jinja2 server-side rendering.
- **Design System**: Implemented Warm Ember (`#f97316`), Deep Slate (`#0f172a`), and modern responsive card layouts.
- **Process Management**: Implemented foundational background task execution hooks and process registry.
</details>
