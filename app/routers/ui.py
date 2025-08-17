import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ..security import require_basic
from ..db import get_session
from ..models import Agent

router = APIRouter()

# Mount static once (at import time)
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui/admin", status_code=307)

@router.get("/ui/admin", response_class=HTMLResponse)
async def admin_ui(request: Request, _=Depends(require_basic)):
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/ui/deployer", response_class=HTMLResponse)
async def deployer_ui(request: Request, _=Depends(require_basic)):
    return templates.TemplateResponse("deployer.html", {
        "request": request,
        "manager_secret_set": bool(os.getenv("MANAGER_SECRET"))
    })

@router.get("/ui/stats", response_class=HTMLResponse)
async def stats_ui(request: Request, _=Depends(require_basic)):
    with get_session() as session:
        agents = session.query(Agent).order_by(Agent.last_seen.desc()).all()
    return templates.TemplateResponse("stats.html", {"request": request, "agents": agents})
