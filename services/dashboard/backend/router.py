from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import BASE_DIR
from services.dashboard.backend.service import get_dashboard_summary

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    summary = get_dashboard_summary()
    return templates.TemplateResponse(
        request=request,
        name="services/dashboard/frontend/templates/dashboard.html",
        context={
            "page_title": "Oasis — Mission Control Dashboard",
            "active_view": "dashboard",
            "summary": summary
        }
    )
