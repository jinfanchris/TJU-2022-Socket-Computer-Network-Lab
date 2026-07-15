"""FastAPI application entrypoint.

Run with:  uvicorn quantpoc.api.app:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from . import rest, ws

app = FastAPI(
    title="quantpoc",
    description="Quantitative-trading POC engine — one API, two clients (web + TUI).",
    version="0.1.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {
        "name": "quantpoc",
        "docs": "/docs",
        "data_mode": settings.data_mode,
        "endpoints": ["/api/health", "/api/meta/indicators", "/api/backtest", "/ws/replay"],
    }
