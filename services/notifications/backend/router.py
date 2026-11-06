from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path
from core.config import BASE_DIR
from services.notifications.backend.service import list_tool_notifications, get_stats, purge_completed_notifications

router = APIRouter(tags=["Notifications"])

templates = Jinja2Templates(directory=[
    str(BASE_DIR / "services" / "notifications" / "frontend" / "templates"),
    str(BASE_DIR / "shared" / "templates")
])

@router.get("/notifications")
async def notifications_page(request: Request, status: str = "ALL", tool: str = "ALL"):
    notifications = list_tool_notifications(status_filter=status, tool_filter=tool)
    stats = get_stats()
    
    return templates.TemplateResponse(
        request=request,
        name="notifications.html",
        context={
            "page_title": "OSINT Processing Notifications — Oasis",
            "active_view": "notifications",
            "notifications": notifications,
            "stats": stats,
            "current_status_filter": status.upper(),
            "current_tool_filter": tool.lower()
        }
    )

@router.get("/api/notifications")
async def get_notifications_api(status: str = "ALL", tool: str = "ALL"):
    notifications = list_tool_notifications(status_filter=status, tool_filter=tool)
    stats = get_stats()
    return JSONResponse(content={
        "status": "success",
        "stats": stats,
        "notifications": notifications
    })

@router.post("/api/notifications/clear")
async def clear_notifications_api():
    result = purge_completed_notifications()
    return JSONResponse(content=result)

