"""
OASIS IP & Network Intelligence Router
FastAPI routes for page rendering, reconnaissance execution, status polling,
history, and evidence dossier downloads.
Strictly isolated under OASIS branding.
"""

from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional

from core.config import BASE_DIR
from services.ip_network_intelligence.backend.service import (
    execute_ip_task,
    get_ip_status,
    get_ip_history,
    ensure_ip_report_file,
    REPORTS_DIR
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class IPRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=256)
    mode: Optional[str] = "flash"
    probe_ports: Optional[bool] = True
    probe_tls: Optional[bool] = True
    probe_headers: Optional[bool] = True
    timeout: Optional[float] = Field(default=1.5, ge=0.5, le=5.0)
    force: Optional[bool] = False

@router.get("/services/ip-network-intelligence", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/ip_network_intelligence/frontend/templates/ip_network_intelligence.html",
        context={
            "page_title": "IP & Network Intelligence — Oasis",
            "active_view": "ip_network_intelligence",
            "initial_target": initial_target
        }
    )

@router.post("/api/ip_network_intelligence/run")
async def run_task(req: IPRunRequest):
    try:
        res = execute_ip_task(
            target=req.target,
            probe_ports=bool(req.probe_ports),
            probe_tls=bool(req.probe_tls),
            probe_headers=bool(req.probe_headers),
            timeout=req.timeout or 1.5,
            force=bool(req.force)
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal IP Intelligence error: {str(e)}")

@router.get("/api/ip_network_intelligence/status")
async def check_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_ip_status(clean_target)

@router.get("/api/ip_network_intelligence/history")
async def get_history():
    return {"history": get_ip_history()}

@router.get("/api/ip_network_intelligence/download")
async def download_report(
    target: str,
    format: str = "json"
):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter is required.")

    fmt = format.lower().strip()
    if fmt not in ["json", "md", "csv"]:
        raise HTTPException(status_code=400, detail="Supported export formats are 'json', 'md', and 'csv'.")

    file_path = ensure_ip_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested dossier does not exist. Run reconnaissance first.")

    media_map = {
        "json": "application/json",
        "csv": "text/csv",
        "md": "text/markdown"
    }
    media_type = media_map.get(fmt, "text/plain")
    filename = f"oasis_network_{file_path.name}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
