from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

from services.email_intelligence.backend.engine_worker import parse_target_emails, is_valid_email
from services.email_intelligence.backend.service import (
    execute_email_recon,
    get_email_status,
    ensure_email_report_file,
    get_recent_email_scans
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR))

class EmailRunRequest(BaseModel):
    target: str = Field(min_length=3, max_length=1500)
    force: Optional[bool] = False
    timeout: Optional[int] = 10
    no_password_recovery: Optional[bool] = False

@router.get("/services/email-intelligence", response_class=HTMLResponse)
async def page_view(request: Request, target: Optional[str] = None):
    initial_target = target.strip() if target else ""
    return templates.TemplateResponse(
        request=request,
        name="services/email_intelligence/frontend/templates/email_intelligence.html",
        context={
            "page_title": "Email Intelligence & Account Footprint — Oasis",
            "active_view": "email_intelligence",
            "initial_target": initial_target
        }
    )

@router.post("/api/email_intelligence/run")
async def run_email_task(req: EmailRunRequest):
    raw_target = req.target.strip()
    if not raw_target:
        raise HTTPException(status_code=400, detail="Target email address cannot be blank.")
    
    parsed = parse_target_emails(raw_target)
    if not parsed:
        raise HTTPException(status_code=400, detail="No valid email address found in input.")

    # Single target
    if len(parsed) == 1:
        target = parsed[0]
        try:
            result = execute_email_recon(
                email=target,
                force=bool(req.force),
                timeout=req.timeout or 10,
                no_password_recovery=bool(req.no_password_recovery)
            )
            result["batch"] = False
            result["parsed_targets"] = parsed
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed dispatching email intelligence task: {e}")

    # Multiple targets (Batch Mode)
    # Start the first email, and return the queue of targets to the client to orchestrate cleanly
    try:
        first_target = parsed[0]
        first_result = execute_email_recon(
            email=first_target,
            force=bool(req.force),
            timeout=req.timeout or 10,
            no_password_recovery=bool(req.no_password_recovery)
        )
        return {
            "status": "BATCH_DISPATCHED",
            "batch": True,
            "total_targets": len(parsed),
            "parsed_targets": parsed,
            "current_target": first_target,
            "first_result": first_result,
            "no_password_recovery": bool(req.no_password_recovery),
            "progress_msg": f"Batch initialized with {len(parsed)} target emails. Processing '{first_target}' first."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed initializing batch email recon: {e}")

@router.get("/api/email_intelligence/status")
async def check_email_status(target: str):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target email parameter is required.")
    return get_email_status(clean_target)

@router.get("/api/email_intelligence/history")
async def fetch_email_history():
    return {"history": get_recent_email_scans()}

@router.get("/api/email_intelligence/download")
async def download_email_report(target: str, format: str = "json"):
    clean_target = target.strip()
    if not clean_target:
        raise HTTPException(status_code=400, detail="Target email parameter is required.")

    fmt = format.lower().strip()
    file_path = ensure_email_report_file(clean_target, fmt)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested OASIS Email Intelligence report does not exist.")

    media_map = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
        "txt": "text/plain"
    }
    media_type = media_map.get(fmt, "application/octet-stream")
    clean_file_key = clean_target.replace('@', '_at_')
    filename = f"OASIS_email_{clean_file_key}_dossier.{fmt}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
