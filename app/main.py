"""FastAPI entry point."""
from __future__ import annotations

import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import orchestrator_tasks, pending, tools
from app.brain.api import brain
from app.bus import bus
from app.db import init_db
from app.routes import cases, meta, sim, stream, victim, webhooks

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    pending.reset()
    tools.reset()
    bus.reset()
    # fire-and-forget model warm-up (daemon thread: never blocks startup or shutdown)
    threading.Thread(target=brain.warm, name="llm-warm", daemon=True).start()
    yield
    await orchestrator_tasks.cancel_all()    # tasks must not outlive the app (tests, reload)


app = FastAPI(title="Golden Hour Guardian", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== ROUTERS (core-engine) =================================================
for _router in (meta.router, webhooks.router, cases.router, victim.router, stream.router, sim.router):
    app.include_router(_router)
# ============================================================================

# Static mounts MUST stay after all API routes, or they shadow them.
@app.get("/")
async def root():
    return FileResponse(WEB / "index.html")

@app.get("/workflow.html")
async def workflow_page():
    return FileResponse(WEB / "workflow.html")

app.mount("/officer", StaticFiles(directory=WEB / "officer", html=True), name="officer")
app.mount("/victim", StaticFiles(directory=WEB / "victim", html=True), name="victim")
