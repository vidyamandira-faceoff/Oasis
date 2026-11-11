from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional

from core.config import BASE_DIR
from services.domain_intelligence.backend.service import (
    execute_domain_task,
    get_domain_status,
    get_domain_history,
    REPORTS_DIR
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class DomainRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=1024)
    depth: Optional[int] = Field(default=2, ge=1, le=4)
    threads: Optional[int] = Field(default=8, ge=1, le=24)
    dns: Optional[bool] = True
    keys: Optional[bool] = True
    wayback: Optional[bool] = False
    force: Optional[bool] = False

@router.get("/services/domain-intelligence", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/domain_intelligence/frontend/templates/domain_intelligence.html",
        context={
            "page_title": "Domain & Website Intelligence — Oasis",
            "active_view": "domain_intelligence",
            "initial_target": initial_target
        }
    )

# Backward-compatibility redirects for previously fragmented routes
@router.get("/services/recon-website-url")
@router.get("/services/recon-subdomains")
@router.get("/services/recon-web-browsers")
async def legacy_surface_redirect():
    return RedirectResponse(url="/services/domain-intelligence", status_code=301)

@router.post("/api/domain_intelligence/run")
async def run_task(req: DomainRunRequest):
    try:
        res = execute_domain_task(
            target=req.target,
            depth=req.depth or 2,
            threads=req.threads or 8,
            dns=bool(req.dns),
            keys=bool(req.keys),
            wayback=bool(req.wayback),
            force=bool(req.force)
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api/domain_intelligence/status")
async def check_status(job_id: str):
    clean_id = job_id.strip()
    if not clean_id:
        raise HTTPException(status_code=400, detail="job_id parameter required.")
    return get_domain_status(clean_id)

@router.get("/api/domain_intelligence/history")
async def search_history():
    return {"history": get_domain_history()}

@router.get("/api/domain_intelligence/download")
async def download_export(job_id: str, format: str = "json"):
    clean_id = job_id.strip()
    output_dir = REPORTS_DIR / clean_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Scan data directory not found.")

    if format.lower() == "json":
        file_path = output_dir / "exported.json"
        media_type = "application/json"
        filename = f"domain_intelligence_{clean_id}.json"
    else:
        file_path = output_dir / "internal.txt"
        media_type = "text/plain"
        filename = f"domain_urls_{clean_id}.txt"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file format not found for this scan.")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )
