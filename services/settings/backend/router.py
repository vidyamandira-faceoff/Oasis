from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import BASE_DIR, SERVICES_DIR, GATEWAY_PORT

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="services/settings/frontend/templates/settings.html",
        context={
            "page_title": "Oasis — Settings & Environments",
            "active_view": "settings",
            "services_dir": str(SERVICES_DIR),
            "gateway_port": GATEWAY_PORT,
            "social_services_count": 4,
            "recon_services_count": 8,
            "total_tools_count": 36
        }
    )
