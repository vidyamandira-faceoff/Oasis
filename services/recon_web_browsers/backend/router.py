from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from core.config import BASE_DIR
from services.recon_web_browsers.backend.service import execute_recon_task, get_latest_findings

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class ReconRunRequest(BaseModel):
    target: str
    tools: Optional[List[str]] = None
    profile: Optional[str] = "deep"

@router.get("/services/recon-web-browsers", response_class=HTMLResponse)
async def page_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="services/recon_web_browsers/frontend/templates/recon_web_browsers.html",
        context={
            "page_title": "Web Footprint & Browser Recon — Oasis",
            "active_view": "recon_web_browsers",
            "default_target": "https://app.targetsite.com"
        }
    )

@router.post("/api/recon_web_browsers/run")
async def run_task(req: ReconRunRequest):
    findings = execute_recon_task(req.target, req.tools, req.profile)
    return {"status": "success", "target": req.target, "findings": findings}

@router.get("/api/recon_web_browsers/results")
async def get_results(target: Optional[str] = None):
    findings = get_latest_findings(target)
    return {"target": target, "findings": findings}
