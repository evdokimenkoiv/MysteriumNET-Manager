import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from .routers import agents, ui
from .db import init_db

app = FastAPI(title="MysteriumNET Manager")

# Static & templates route mounting happens in ui router
app.include_router(ui.router, tags=["ui"])
app.include_router(agents.router, tags=["agents"])

@app.on_event("startup")
async def on_startup():
    init_db()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
