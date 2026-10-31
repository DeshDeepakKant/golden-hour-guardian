"""FastAPI entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Golden Hour Guardian", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "llm": "unknown"}


# ===== ROUTERS (core-engine fills this block) ===============================
# from app.routes import cases, sim, ...
# app.include_router(cases.router)
# ============================================================================

# Static mounts MUST stay after all API routes, or they shadow them.
app.mount("/officer", StaticFiles(directory=WEB / "officer", html=True), name="officer")
app.mount("/victim", StaticFiles(directory=WEB / "victim", html=True), name="victim")
