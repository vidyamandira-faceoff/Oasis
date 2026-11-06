import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import (
    BASE_DIR,
    GATEWAY_PORT,
    APP_NAME,
    APP_VERSION
)
from core.process_manager import RUNNING_PROCESSES, terminate_all_tasks

# Core Services Routers
from services.dashboard.backend.router import router as dashboard_router
from services.vault.backend.router import router as vault_router
from services.terminal.backend.router import router as terminal_router
from services.settings.backend.router import router as settings_router
from services.notifications.backend.router import router as notifications_router

# Social Media Scraping & Recon Routers
from services.social_instagram.backend.router import router as social_instagram_router
from services.social_linkedin.backend.router import router as social_linkedin_router
from services.social_x.backend.router import router as social_x_router
from services.social_reddit.backend.router import router as social_reddit_router

# Reconnaissance & Footprinting Routers
from services.recon_website_url.backend.router import router as recon_website_url_router
from services.recon_web_browsers.backend.router import router as recon_web_browsers_router
from services.recon_email.backend.router import router as recon_email_router
from services.recon_ip.backend.router import router as recon_ip_router
from services.recon_username.backend.router import router as recon_username_router
from services.recon_phone.backend.router import router as recon_phone_router
from services.recon_subdomains.backend.router import router as recon_subdomains_router
from services.recon_crypto.backend.router import router as recon_crypto_router

app = FastAPI(
    title=APP_NAME,
    description="Unified Modular Reconnaissance & Scraping Architecture with Background Multi-Tool Engines",
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
        "engines_ready": 12,
        "services": {
            "social": ["instagram", "linkedin", "x", "reddit"],
            "recon": [
                "website_url",
                "web_browsers",
                "email",
                "ip",
                "username",
                "phone",
                "subdomains",
                "crypto"
            ]
        }
    }

@app.post("/api/tools/abort-all")
async def abort_all_tasks():
    return terminate_all_tasks()

# -----------------------------------------------------------------------------
# Microservice Routers Registration
# -----------------------------------------------------------------------------
# Core
app.include_router(dashboard_router)
app.include_router(vault_router)
app.include_router(terminal_router)
app.include_router(settings_router)
app.include_router(notifications_router)

# Social Media
app.include_router(social_instagram_router)
app.include_router(social_linkedin_router)
app.include_router(social_x_router)
app.include_router(social_reddit_router)

# Reconnaissance & Footprinting
app.include_router(recon_website_url_router)
app.include_router(recon_web_browsers_router)
app.include_router(recon_email_router)
app.include_router(recon_ip_router)
app.include_router(recon_username_router)
app.include_router(recon_phone_router)
app.include_router(recon_subdomains_router)
app.include_router(recon_crypto_router)

if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting Oasis OSINT Gateway on http://127.0.0.1:{GATEWAY_PORT} ...")
    uvicorn.run("server:app", host="127.0.0.1", port=GATEWAY_PORT, reload=True)
