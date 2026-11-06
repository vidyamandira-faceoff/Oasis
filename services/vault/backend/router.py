import time
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import BASE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

# Standard aggregate sample vault items across social and recon services
_DEFAULT_VAULT_ENTITIES = [
    {
        "name": "belurmath.org",
        "engine": "Website URL Recon",
        "service_url": "/services/recon-website-url?target=belurmath.org",
        "badge": "URL",
        "badge_color": "var(--primary)",
        "asset_count": "86,120 items",
        "last_modified": "2026-11-03 12:41:00",
        "category": "Web Recon"
    },
    {
        "name": "animeschedule.net",
        "engine": "Subdomain Recon",
        "service_url": "/services/recon-subdomains?target=animeschedule.net",
        "badge": "SUB",
        "badge_color": "var(--success)",
        "asset_count": "14 hostnames",
        "last_modified": "2026-11-02 21:11:00",
        "category": "DNS"
    },
    {
        "name": "@veritasium_daily",
        "engine": "Instagram Intelligence",
        "service_url": "/services/social-instagram",
        "badge": "IG",
        "badge_color": "#c026d3",
        "asset_count": "Profile & Network Graph",
        "last_modified": "2026-11-04 18:22:00",
        "category": "Social"
    },
    {
        "name": "104.21.55.2",
        "engine": "IP Intelligence",
        "service_url": "/services/recon-ip",
        "badge": "IP",
        "badge_color": "#0d9488",
        "asset_count": "Cloudflare ASN 13335",
        "last_modified": "2026-11-05 14:15:00",
        "category": "Network"
    },
    {
        "name": "Global Defense Technologies",
        "engine": "LinkedIn Recon",
        "service_url": "/services/social-linkedin",
        "badge": "IN",
        "badge_color": "#0077b5",
        "asset_count": "Workforce OrgChart",
        "last_modified": "2026-11-05 16:40:00",
        "category": "Corporate"
    },
    {
        "name": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "engine": "Bitcoin & Crypto Recon",
        "service_url": "/services/recon-crypto",
        "badge": "BTC",
        "badge_color": "#f7931a",
        "asset_count": "1.42 BTC Balance",
        "last_modified": "2026-11-05 19:10:00",
        "category": "Blockchain"
    }
]

@router.get("/vault", response_class=HTMLResponse)
async def vault_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="services/vault/frontend/templates/vault.html",
        context={
            "page_title": "Oasis — Target Vault",
            "active_view": "vault",
            "entities": _DEFAULT_VAULT_ENTITIES
        }
    )
