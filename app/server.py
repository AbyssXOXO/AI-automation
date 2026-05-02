from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query

from app.config import settings
from app.scanner import periodic_scan_loop, scan_if_due, scan_sources, start_background_scan
from app.state import state
from app.utils import iso_now


@asynccontextmanager
async def lifespan(_: FastAPI):
    task: asyncio.Task[None] | None = None
    if settings.background_loop:
        task = asyncio.create_task(periodic_scan_loop())
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def create_app() -> FastAPI:
    api = FastAPI(
        title="AI News Automation Bot",
        description="Fetches RSS/scraped items, filters them with Gemini, and sends Telegram alerts.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @api.get("/")
    async def root() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "AI News Automation Bot",
            "endpoints": ["/ping", "/scan", "/state"],
        }

    @api.get("/ping")
    async def ping(
        scan: bool = Query(False, description="Run a due scan after pinging."),
        background: bool = Query(False, description="Run the due scan in the background."),
    ) -> dict[str, Any]:
        if not scan:
            return {"status": "ok", "time": iso_now()}
        if background:
            return start_background_scan(due_only=True)
        return await scan_if_due()

    @api.api_route("/scan", methods=["GET", "POST"])
    async def scan_endpoint(
        force: bool = Query(False, description="Reprocess already-seen links."),
        background: bool = Query(False, description="Start scan and return immediately."),
    ) -> dict[str, Any]:
        if background:
            return start_background_scan(force=force)
        return await scan_sources(force=force)

    @api.get("/state")
    async def state_endpoint() -> dict[str, Any]:
        return {
            "last_scan_at": state.data.get("last_scan_at"),
            "seen_count": len(state.data.get("seen_items", [])),
            "last_results": state.data.get("last_results", []),
            "configured": {
                "rss_sources": [source["name"] for source in settings.rss_sources],
                "scrape_targets": [target.get("name") or target.get("url") for target in settings.scrape_targets],
                "gemini": bool(settings.gemini_api_key),
                "telegram": bool(settings.telegram_bot_token and settings.telegram_chat_id),
                "target_companies": settings.target_companies,
                "background_loop": settings.background_loop,
                "scan_interval_minutes": settings.scan_interval_minutes,
            },
        }

    return api

