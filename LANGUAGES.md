# Oasis — Languages & Technologies Architecture

This document details all programming languages, templating engines, styling specifications, frameworks, and deployment scripts used across the entire **Oasis** platform, categorized by architectural tier.

---

## 1. Frontend Layer (User Interface & Presentation)

* **HTML5 (`.html`)**:
  * Semantic HTML5 markup structuring the unified command shell, tactical sidebar, dynamic dashboards, interactive data tables, tabbed panels, and modals.
* **Jinja2 Templating Language (`.html` templates)**:
  * Server-side templating engine used to stitch the layouts together dynamically.
  * Allows template inheritance (`{% extends "shared/templates/base.html" %}`), conditional active-route highlighting, safe variable rendering, and component reusability across all service views without client-side lag.
* **CSS3 (`.css`)**:
  * Custom design system with dedicated dark mode stylesheets (`dark_mode.css`) for each microservice.
  * **CSS Custom Properties (Variables)** for the warm ember accent system (`--ember-500: #f97316`), soft background neutrals, and deep obsidian dark surfaces.
  * Modern layout engines: **CSS Grid** (for KPI bento grids) and **Flexbox** (for alignment, header capsules, and sidebars).
  * Smooth animations and transitions (`cubic-bezier` timing curves, subtle hover lift effects, and glowing indicators).
* **JavaScript (Vanilla ECMAScript 6+ / `.js`)**:
  * Pure client-side JavaScript without bulky external libraries to guarantee instant loading.
  * **Asynchronous Web APIs (`fetch`)**: For non-blocking REST API calls to launch background multi-tool engines, fetch streaming telemetry, and export findings.
  * **DOM & Event APIs**: Real-time clock updates, search-bar keyboard shortcuts, dark/light theme switcher with `localStorage` persistence, and collapsible filters.
* **SVG (Scalable Vector Graphics)**:
  * Inline vector graphics for all tactical iconography ensuring crisp rendering on high-DPI displays.

---

## 2. Middleware & Gateway Layer

* **Python 3 (Starlette ASGI Middleware)**:
  * **FastAPI / Starlette Middleware**: Manages the request/response lifecycle, error interception, route routing, and status code generation.
  * **Static Asset Middleware (`StaticFiles`)**: Mounts and securely serves shared and service-specific CSS/JS assets across custom virtual routes (`/static/shared`, `/static/services/{service_name}`, etc.).
  * **In-Memory Telemetry Ring Buffer (`collections.deque` in Python)**: A non-blocking FIFO circular buffer that captures subprocess logs and streams them to the `/terminal` view without disk I/O bottlenecks.

---

## 3. Backend Layer (Modular Services & Background Engines)

* **Python 3.10+ (`.py`)**:
  * **Web Framework**: **FastAPI** — high-performance, asynchronous web framework built on top of Starlette and Pydantic.
  * **Modular Service Routers (`APIRouter`)**: Each service (`services/social_instagram`, `services/recon_website_url`, `services/recon_ip`, etc.) has its own isolated `router.py` (API endpoints) and `service.py` (business logic) following separation-of-concerns principles.
  * **Background Multi-Tool Engines**: Under each service directory, specialized background engine subdirectories (`tools/<engine_name>/engine.py`) execute dedicated data extraction, scraping, and correlation workflows concurrently.
  * **Cross-Platform Process Manager (`core/process_manager.py`)**:
    * Dynamically handles OS-specific process termination (`taskkill /F /T` on Windows; `os.killpg()` on Linux/Unix).

---

## 4. Data, Query & Storage Layer

* **JSON (`.json`)**:
  * Used for internal REST API communication payloads and client-side data export.
* **In-Memory & SQLite Cache**:
  * Thread-safe in-memory cache and local repository storing extracted entities, historical targets, and telemetry events.
