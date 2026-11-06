from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from core.config import BASE_DIR
from services.social_x.backend.service import execute_recon_task, get_latest_findings

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class ReconRunRequest(BaseModel):
    target: str
    tools: Optional[List[str]] = None
    profile: Optional[str] = "deep"

@router.get("/services/social-x", response_class=HTMLResponse)
async def page_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="services/social_x/frontend/templates/social_x.html",
        context={
            "page_title": "X (Twitter) Scraping & Recon — Oasis",
            "active_view": "social_x",
            "default_target": "@cyber_intel"
        }
    )

@router.post("/api/social_x/run")
async def run_task(req: ReconRunRequest):
    findings = execute_recon_task(req.target, req.tools, req.profile)
    return {"status": "success", "target": req.target, "findings": findings}

@router.get("/api/social_x/results")
async def get_results(target: Optional[str] = None):
    findings = get_latest_findings(target)
    return {"target": target, "findings": findings}
