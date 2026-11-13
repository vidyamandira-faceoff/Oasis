import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from core.config import (
    BASE_DIR,
    GATEWAY_PORT,
    APP_NAME,
    APP_VERSION
)
from core.process_manager import RUNNING_PROCESSES, terminate_all_tasks

# Core Services Routers
from services.dashboard.backend.router import router as dashboard_router
from services.settings.backend.router import router as settings_router
from services.notifications.backend.router import router as notifications_router
from services.changelog.backend.router import router as changelog_router
# Active Intelligence Module Routers
from services.recon_username.backend.router import router as recon_username_router
from services.domain_intelligence.backend.router import router as domain_intelligence_router
from services.social_media_intelligence.backend.router import router as social_media_router
from services.phone_intelligence.backend.router import router as phone_intelligence_router
from services.email_intelligence.backend.router import router as email_intelligence_router
from services.ip_network_intelligence.backend.router import router as ip_network_router

app = FastAPI(
    title=APP_NAME,
    description="OASIS — Open-source OSINT Investigation Platform (V1 Demo Build)",
    version=APP_VERSION
)

# -----------------------------------------------------------------------------
# Static Assets Mounts (Shared + Module Specific)
# -----------------------------------------------------------------------------
shared_static_dir = BASE_DIR / "shared" / "static"
if shared_static_dir.exists():
    app.mount("/static/shared", StaticFiles(directory=str(shared_static_dir)), name="shared_static")

services_dir = BASE_DIR / "services"
if services_dir.exists():
    for mod_dir in services_dir.iterdir():
        if mod_dir.is_dir():
            mod_static = mod_dir / "frontend" / "static"
            if mod_static.exists():
                app.mount(f"/static/services/{mod_dir.name}", StaticFiles(directory=str(mod_static)), name=f"{mod_dir.name}_static")

root_static_dir = BASE_DIR / "static"
if root_static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(root_static_dir)), name="root_static")

# -----------------------------------------------------------------------------
# Global Health & Status API
# -----------------------------------------------------------------------------
@app.get("/api/status")
async def get_system_status():
    return {
        "status": "operational",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_processes": len(RUNNING_PROCESSES),
        "active_modules": [
            "Username Intelligence",
            "Domain & Website Intelligence",
            "Social Media Intelligence",
            "Phone Number Intelligence",
            "Email Intelligence",
            "IP & Network Intelligence",
        ],
        "connected_engines": [
            "OASIS Username Intelligence Engine",
            "OASIS Domain & Website Intelligence Engine",
            "OASIS Instagram Flash Scraper (Chromium Headless)",
            "OASIS Email Intelligence Engine",
            "OASIS IP & Network Intelligence Engine",
            "Native Social Media Scraper Cluster",
            "Native Phone Number Intelligence Platform",
        ],
    }

@app.post("/api/tools/abort-all")
async def abort_all_tasks():
    return terminate_all_tasks()

# -----------------------------------------------------------------------------
# Microservice Routers Registration
# -----------------------------------------------------------------------------
# Core Platform Modules
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(notifications_router)
app.include_router(changelog_router)

# Legacy view redirects (decommissioned /vault and /terminal)
@app.get("/vault")
async def redirect_vault():
    return RedirectResponse(url="/changelog", status_code=302)

@app.get("/terminal")
async def redirect_terminal():
    return RedirectResponse(url="/changelog", status_code=302)

# Intelligence Modules
app.include_router(recon_username_router)
app.include_router(domain_intelligence_router)
app.include_router(social_media_router)
app.include_router(phone_intelligence_router)
app.include_router(email_intelligence_router)
app.include_router(ip_network_router)

# -----------------------------------------------------------------------------
# Root Fallback Redirect
# -----------------------------------------------------------------------------
@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=GATEWAY_PORT, reload=True)
