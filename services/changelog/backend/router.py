"""
Changelog API & Web Router for OASIS
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, PlainTextResponse
from core.config import BASE_DIR
from services.changelog.backend.service import (
    get_all_releases,
    get_latest_version,
    get_changelog_markdown
)

router = APIRouter(tags=["Platform Changelog"])

templates = Jinja2Templates(directory=str(BASE_DIR))

@router.get("/changelog")
async def changelog_page(request: Request):
    """Renders the OASIS interactive release history and semantic changelog portal."""
    releases = get_all_releases()
    latest_version = get_latest_version()
    
    return templates.TemplateResponse(
        request=request,
        name="services/changelog/frontend/templates/changelog.html",
        context={
            "page_title": "Platform Changelog & Releases — Oasis",
            "active_view": "changelog",
            "releases": releases,
            "latest_version": latest_version,
            "total_releases": len(releases),
        }
    )

@router.get("/api/changelog")
async def get_changelog_api():
    """Returns structured JSON of all platform releases and changes."""
    return JSONResponse(content={
        "status": "success",
        "latest_version": get_latest_version(),
        "releases": get_all_releases()
    })

@router.get("/api/changelog/raw")
async def get_raw_changelog_markdown():
    """Returns raw CHANGELOG.md file content."""
    return PlainTextResponse(content=get_changelog_markdown(), media_type="text/markdown")
