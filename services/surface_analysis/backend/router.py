from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Dict, Optional

from core.config import BASE_DIR
from services.surface_analysis.backend.service import (
    MODULES,
    get_job,
    get_module,
    list_jobs,
    start_analysis,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))


class AnalysisRequest(BaseModel):
    target: str = Field(min_length=1, max_length=2048)
    level: int = Field(default=2, ge=1, le=5)
    threads: int = Field(default=6, ge=1, le=30)
    keys: bool = False
    dns: bool = False
    wayback: bool = False
    only_urls: bool = False
    regex: Optional[str] = Field(default=None, max_length=500)
    exclude: Optional[str] = Field(default=None, max_length=500)
    timeout: int = Field(default=900, ge=30, le=3600)


def _page_context(module: str) -> Dict:
    config = get_module(module)
    return {
        "page_title": f"Oasis — {config['title']}",
        "active_view": config["view"],
        "module": module,
        "module_config": config,
    }


for _module, _config in MODULES.items():
    def page(request: Request, module: str = _module):
        return templates.TemplateResponse(
            request=request,
            name="services/surface_analysis/frontend/templates/module.html",
            context=_page_context(module),
        )

    router.add_api_route(_config["route"], page, methods=["GET"], response_class=HTMLResponse)


@router.post("/api/surface/{module}/run")
async def run_analysis(module: str, request: AnalysisRequest):
    if module not in MODULES:
        raise HTTPException(status_code=404, detail="Unknown surface analysis module.")
    try:
        return start_analysis(module, request.target, request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/surface/{module}/jobs")
async def get_jobs(module: str):
    if module not in MODULES:
        raise HTTPException(status_code=404, detail="Unknown surface analysis module.")
    return {"jobs": list_jobs(module)}


@router.get("/api/surface/jobs/{job_id}")
async def get_analysis_job(job_id: str):
    try:
        return get_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
