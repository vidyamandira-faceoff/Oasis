import re
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from core.config import BASE_DIR
from services.social_media_intelligence.backend.service import (
    execute_social_task,
    get_social_status,
    get_social_history,
    ensure_social_report_file,
    execute_instagram_task,
    get_instagram_status,
    ensure_instagram_report_file,
    execute_twitter_task,
    get_twitter_status,
    ensure_twitter_report_file,
    NATIVE_SCRAPER_ENDPOINTS,
    REPORTS_DIR
)

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR))

class SocialRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=100)
    mode: Optional[str] = "pro"       # "flash", "pro", "ultra", "max"
    platform: Optional[str] = "all"   # "all", "instagram", "facebook", "twitter", "linkedin"
    force: Optional[bool] = False

@router.get("/services/social-media-intelligence", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/social_media_intelligence/frontend/templates/social_media_intelligence.html",
        context={
            "page_title": "Social Media Intelligence & Account Analysis — Oasis",
            "active_view": "social_media_intelligence",
            "initial_target": initial_target,
            "native_endpoints": NATIVE_SCRAPER_ENDPOINTS
        }
    )

@router.post("/api/social_media_intelligence/run")
async def run_task(req: SocialRunRequest):
    target = req.target.strip()
    if not target:
        raise HTTPException(status_code=400, detail="Target handle or identifier cannot be blank.")

    # Validation: Alphanumeric, underscores, dots, hyphens
    if not re.match(r'^[a-zA-Z0-9_\-\.:]{1,100}$', target):
        raise HTTPException(status_code=400, detail="Invalid target format. Use alphanumeric characters, dots, underscores, or hyphens.")

    result = execute_social_task(
        target=target,
        mode=req.mode or "pro",
        platform=req.platform or "all",
        force=bool(req.force)
    )
    return result

@router.get("/api/social_media_intelligence/status")
async def check_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_social_status(clean_target)

@router.get("/api/social_media_intelligence/history")
async def get_history():
    return {"history": get_social_history()}

@router.get("/api/social_media_intelligence/native-endpoints")
async def get_native_endpoints():
    return {"endpoints": NATIVE_SCRAPER_ENDPOINTS}

@router.get("/api/social_media_intelligence/download")
async def download_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")

    fmt = format.lower().strip()
    file_path = ensure_social_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested report file does not exist and could not be generated.")

    media_map = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain"
    }
    media_type = media_map.get(fmt, "text/plain")
    filename = f"social_intelligence_{clean_target}.{fmt}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# -----------------------------------------------------------------------------
# Dedicated OASIS Instagram Scraper Routes (Flash vs Pro Modes)
# -----------------------------------------------------------------------------
class InstagramRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=150)
    mode: Optional[str] = "flash"              # "flash" (local OASIS engine) or "pro" (native cluster)
    count: Optional[int] = 8
    target_type: Optional[str] = "user"        # "user", "post", "hashtag", "location"
    comments: Optional[bool] = False          # Deep comment extraction per post
    download_zip: Optional[bool] = False      # Download offline media ZIP archive
    proxy: Optional[str] = ""                 # Optional HTTP/SOCKS5 proxy server
    session: Optional[str] = ""               # Optional session cookie
    force: Optional[bool] = False

@router.post("/api/social_media_intelligence/instagram/run")
async def run_instagram_task(req: InstagramRunRequest):
    target = req.target.strip()
    if not target:
        raise HTTPException(status_code=400, detail="Target Instagram handle or URL cannot be blank.")
    
    result = execute_instagram_task(
        target=target,
        mode=req.mode or "flash",
        count=req.count or 8,
        target_type=req.target_type or "user",
        comments=bool(req.comments),
        session=req.session or "",
        proxy=req.proxy or "",
        download_zip=bool(req.download_zip),
        force=bool(req.force)
    )
    return result

@router.get("/api/social_media_intelligence/instagram/status")
async def check_instagram_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_instagram_status(clean_target)

@router.get("/api/social_media_intelligence/instagram/download")
async def download_instagram_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")

    fmt = format.lower().strip()
    file_path = ensure_instagram_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested OASIS Instagram report file does not exist.")

    media_map = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain",
        "zip": "application/zip"
    }
    media_type = media_map.get(fmt, "application/octet-stream")
    ext = "zip" if fmt == "zip" else fmt
    filename = f"OASIS_instagram_{clean_target}_{'media' if fmt == 'zip' else 'dossier'}.{ext}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# -----------------------------------------------------------------------------
# Dedicated OASIS X / Twitter Scraper Routes (Flash vs Pro Modes)
# -----------------------------------------------------------------------------
class TwitterRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=200)
    mode: Optional[str] = "flash"              # "flash" (twscrape) or "pro" (native cluster)
    count: Optional[int] = 10
    target_type: Optional[str] = "user"        # "user", "search", "hashtag", "tweet"
    session: Optional[str] = ""               # Optional auth_token=...; ct0=...
    proxy: Optional[str] = ""                 # Optional HTTP/SOCKS5 proxy
    force: Optional[bool] = False

@router.post("/api/social_media_intelligence/twitter/run")
async def run_twitter_task(req: TwitterRunRequest):
    target = req.target.strip()
    if not target:
        raise HTTPException(status_code=400, detail="Target X / Twitter handle, query, or URL cannot be blank.")
    
    result = execute_twitter_task(
        target=target,
        mode=req.mode or "flash",
        count=req.count or 10,
        target_type=req.target_type or "user",
        session=req.session or "",
        proxy=req.proxy or "",
        force=bool(req.force)
    )
    return result

@router.get("/api/social_media_intelligence/twitter/status")
async def check_twitter_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")
    return get_twitter_status(clean_target)

@router.get("/api/social_media_intelligence/twitter/download")
async def download_twitter_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target parameter required.")

    fmt = format.lower().strip()
    file_path = ensure_twitter_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested OASIS Twitter report file does not exist.")

    media_map = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain"
    }
    media_type = media_map.get(fmt, "application/octet-stream")
    clean_file_key = clean_target.replace('@', '').replace('/', '_')
    filename = f"OASIS_twitter_{clean_file_key}_dossier.{fmt}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


