##Core Orchestration Engine.
#This is the central traffic controller of the bot. It pulls everything together:
#it calls the fetchers, filters out items we've already seen, spaces out the 
#requests to the Gemini API to avoid rate limits, and triggers the Telegram 
#notifications. It also uses async locks to ensure we don't accidentally run 
#multiple scans at the exact same time.

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any

from app.ai_gatekeeper import evaluate_with_gemini
from app.config import settings
from app.fetchers import gather_items
from app.notifier import send_telegram
from app.state import state
from app.utils import iso_now, utc_now


scan_lock = asyncio.Lock()
last_background_task: asyncio.Task[dict[str, Any]] | None = None


async def scan_sources(force: bool = False) -> dict[str, Any]:
    if scan_lock.locked():
        return {"status": "busy", "started": False, "message": "A scan is already running."}

    async with scan_lock:
        if not settings.gemini_api_key:
            return {
                "status": "misconfigured",
                "started": False,
                "message": "Set GEMINI_API_KEY or API_KEY before running scans.",
            }

        started_at = iso_now()
        fetched_items, fetch_errors = await gather_items()
        seen = state.seen_items
        candidates = [item for item in fetched_items if force or item.item_id not in seen]
        candidates = candidates[: settings.max_items_per_scan]

        notifications: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        processed_ids: list[str] = []

        for index, item in enumerate(candidates):
            # ADD THIS BLOCK: Sleep between requests (but skip the first one)
            if index > 0:
                await asyncio.sleep(settings.gemini_request_delay)
                
            try:
                decision = await evaluate_with_gemini(item)
            except Exception as exc:  # noqa: BLE001
                skipped.append({"title": item.title, "url": item.url, "reason": f"Gemini error: {exc}"})
                continue

            record = {
                "item": asdict(item),
                "decision": decision,
            }
            if decision["relevant"]:
                try:
                    sent = await send_telegram(item, decision)
                    record["telegram_error"] = None
                except Exception as exc:  # noqa: BLE001 - record notification failures without losing the scan.
                    sent = False
                    record["telegram_error"] = str(exc)
                record["telegram_sent"] = sent
                if sent:
                    processed_ids.append(item.item_id)
                notifications.append(record)
            else:
                processed_ids.append(item.item_id)
                skipped.append(
                    {
                        "title": item.title,
                        "url": item.url,
                        "score": decision.get("score"),
                        "reason": decision.get("reason"),
                    }
                )

        result = {
            "status": "completed",
            "started": True,
            "started_at": started_at,
            "finished_at": iso_now(),
            "fetched": len(fetched_items),
            "new_candidates": len(candidates),
            "notifications_sent": sum(1 for item in notifications if item.get("telegram_sent")),
            "notifications": notifications,
            "skipped": skipped[:20],
            "fetch_errors": fetch_errors,
        }
        state.mark_seen(processed_ids)
        state.set_last_scan(result)
        return result


def last_scan_due() -> bool:
    raw = state.data.get("last_scan_at")
    if not raw:
        return True
    try:
        last_scan = datetime.fromisoformat(raw)
    except ValueError:
        return True
    age_seconds = (utc_now() - last_scan).total_seconds()
    return age_seconds >= settings.scan_interval_minutes * 60


async def scan_if_due() -> dict[str, Any]:
    if not last_scan_due():
        return {
            "status": "skipped",
            "reason": "Scan interval has not elapsed.",
            "last_scan_at": state.data.get("last_scan_at"),
            "scan_interval_minutes": settings.scan_interval_minutes,
        }
    return await scan_sources(force=False)


async def periodic_scan_loop() -> None:
    if settings.startup_scan:
        await scan_sources(force=False)
    while True:
        await asyncio.sleep(settings.scan_interval_minutes * 60)
        await scan_sources(force=False)


def start_background_scan(force: bool = False, due_only: bool = False) -> dict[str, Any]:
    global last_background_task
    if last_background_task and not last_background_task.done():
        return {"status": "busy", "message": "A background scan is already running."}
    coro = scan_if_due() if due_only else scan_sources(force=force)
    last_background_task = asyncio.create_task(coro)
    return {"status": "accepted", "background": True, "started_at": iso_now()}

