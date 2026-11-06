from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from core.config import BASE_DIR
from services.recon_email.backend.service import execute_recon_task, get_latest_findings

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class ReconRunRequest(BaseModel):
    target: str
    tools: Optional[List[str]] = None
    profile: Optional[str] = "deep"

@router.get("/services/recon-email", response_class=HTMLResponse)
async def page_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="services/recon_email/frontend/templates/recon_email.html",
        context={
            "page_title": "Email Address Scraping & Recon — Oasis",
            "active_view": "recon_email",
            "default_target": "analyst@targetdomain.com"
        }
    )

@router.post("/api/recon_email/run")
async def run_task(req: ReconRunRequest):
    findings = execute_recon_task(req.target, req.tools, req.profile)
    return {"status": "success", "target": req.target, "findings": findings}

@router.get("/api/recon_email/results")
async def get_results(target: Optional[str] = None):
    findings = get_latest_findings(target)
    return {"target": target, "findings": findings}
