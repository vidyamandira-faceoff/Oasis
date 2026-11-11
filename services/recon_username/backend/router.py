import re
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from core.config import BASE_DIR
from services.recon_username.backend.service import (
    execute_recon_task,
    get_recon_status,
    get_latest_findings,
    REPORTS_DIR
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class ReconRunRequest(BaseModel):
    target: str
    scope: Optional[str] = "standard"  # "quick", "standard", "deep"
    category: Optional[str] = "all"    # "all", "coding", "social", "business", etc.
    timeout: Optional[int] = 6
    force: Optional[bool] = False

@router.get("/services/recon-username", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/recon_username/frontend/templates/recon_username.html",
        context={
            "page_title": "Username Intelligence & Identity Reconnaissance — Oasis",
            "active_view": "recon_username",
            "initial_target": initial_target
        }
    )

@router.post("/api/recon_username/run")
async def run_task(req: ReconRunRequest):
    target = req.target.strip()
    if not target:
        raise HTTPException(status_code=400, detail="Target username cannot be blank.")
    
    # Safe username validation (standard handles: alphanumeric, underscores, hyphens, dots)
    if not re.match(r'^[a-zA-Z0-9_\-\.]{1,100}$', target):
        raise HTTPException(status_code=400, detail="Invalid target format. Use alphanumeric characters, dots, underscores, or hyphens.")
        
    result = execute_recon_task(
        target=target,
        scope=req.scope or "standard",
        category=req.category or "all",
        timeout=req.timeout or 6,
        force=bool(req.force)
    )
    return result

@router.get("/api/recon_username/status")
async def check_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_recon_status(clean_target)

@router.get("/api/recon_username/results")
async def get_results(target: Optional[str] = None):
    clean_target = target.strip() if target else ""
    findings = get_latest_findings(clean_target)
    return {"target": clean_target, "findings": findings}

@router.get("/api/recon_username/download")
async def download_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")

    fmt = format.lower().strip()
    if fmt == "csv":
        file_path = REPORTS_DIR / f"report_{clean_target}.csv"
        media_type = "text/csv"
        filename = f"recon_{clean_target}_report.csv"
    elif fmt == "html":
        file_path = REPORTS_DIR / f"report_{clean_target}_plain.html"
        media_type = "text/html"
        filename = f"recon_{clean_target}_report.html"
    elif fmt == "txt":
        file_path = REPORTS_DIR / f"report_{clean_target}.txt"
        media_type = "text/plain"
        filename = f"recon_{clean_target}_report.txt"
    else:
        file_path = REPORTS_DIR / f"report_{clean_target}_simple.json"
        media_type = "application/json"
        filename = f"recon_{clean_target}_report.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested report file does not exist for this target.")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )
