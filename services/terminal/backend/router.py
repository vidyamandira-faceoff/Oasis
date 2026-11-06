from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import BASE_DIR
from core.logger import get_logs, clear_logs

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

@router.get("/terminal", response_class=HTMLResponse)
async def terminal_page(request: Request):
    logs = get_logs(150)
    return templates.TemplateResponse(
        request=request,
        name="services/terminal/frontend/templates/terminal.html",
        context={
            "page_title": "Oasis — Live Terminal",
            "active_view": "terminal",
            "logs": logs
        }
    )

@router.get("/api/terminal/logs")
async def api_logs():
    return {"logs": get_logs(150)}

@router.post("/api/terminal/clear")
async def api_clear():
    clear_logs()
    return {"message": "Logs cleared"}

