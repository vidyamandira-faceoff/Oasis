import re
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional

from core.config import BASE_DIR
from services.phone_intelligence.backend.service import (
    execute_phone_task,
    get_phone_status,
    get_phone_history,
    ensure_phone_report_file,
    NATIVE_PHONE_ENDPOINT,
    REPORTS_DIR
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class PhoneRunRequest(BaseModel):
    target: str = Field(min_length=3, max_length=50)
    country: Optional[str] = "IN"
    force: Optional[bool] = False

@router.get("/services/phone-intelligence", response_class=HTMLResponse)
@router.get("/services/recon-phone", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/phone_intelligence/frontend/templates/phone_intelligence.html",
        context={
            "page_title": "Phone Number Intelligence & Carrier Profiler — Oasis",
            "active_view": "phone_intelligence",
            "initial_target": initial_target,
            "native_endpoint": NATIVE_PHONE_ENDPOINT
        }
    )

@router.post("/api/phone_intelligence/run")
async def run_task(req: PhoneRunRequest):
    clean_target = req.target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target phone number cannot be blank.")

    try:
        result = execute_phone_task(
            target=clean_target,
            default_country=req.country or "IN",
            force=bool(req.force)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Phone intelligence execution failed: {str(e)}")

@router.get("/api/phone_intelligence/status")
async def check_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_phone_status(clean_target)

@router.get("/api/phone_intelligence/history")
async def get_history():
    return {"history": get_phone_history()}

@router.get("/api/phone_intelligence/native-endpoint")
async def get_native_endpoint():
    return {"endpoint": NATIVE_PHONE_ENDPOINT}

@router.get("/api/phone_intelligence/download")
async def download_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")

    fmt = format.lower().strip()
    file_path = ensure_phone_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested report file does not exist and could not be generated.")

    media_map = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain"
    }
    media_type = media_map.get(fmt, "text/plain")
    filename = f"phone_intelligence_{clean_target}.{fmt}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
