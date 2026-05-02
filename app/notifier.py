from __future__ import annotations

from html import escape
from typing import Any

from telegram import Bot

from app.config import settings
from app.models import NewsItem
from app.utils import clean_text


def build_telegram_message(item: NewsItem, decision: dict[str, Any]) -> str:
    company = clean_text(str(decision.get("company") or item.company or "Big Tech"))
    opportunity_type = clean_text(str(decision.get("opportunity_type") or item.category or "opportunity"))
    alert_title = clean_text(str(decision.get("title") or item.title))
    deadline = clean_text(str(decision.get("deadline") or "Unknown"))
    prize = clean_text(str(decision.get("prize") or "Unknown"))
    cost = clean_text(str(decision.get("cost") or "Unknown"))
    why_you_care = clean_text(str(decision.get("why_you_care") or ""))
    action_url = clean_text(str(decision.get("action_url") or item.url))
    tags = " ".join(f"#{clean_text(str(tag)).replace(' ', '')}" for tag in decision.get("tags", [])[:4])
    parts = [
        f"<b>New {escape(company)} opportunity</b>",
        f"<b>Type:</b> {escape(opportunity_type)}",
        f"<b>Title:</b> {escape(alert_title)}",
        f"<i>{escape(item.source)}</i>",
        "",
        escape(clean_text(str(decision.get("summary") or item.text), 700)),
    ]
    if deadline and deadline.lower() != "unknown":
        parts.append(f"<b>Deadline:</b> {escape(deadline)}")
    if cost and cost.lower() != "unknown":
        parts.append(f"<b>Cost:</b> {escape(cost)}")
    if prize and prize.lower() != "unknown":
        parts.append(f"<b>Prize/Certificate:</b> {escape(prize)}")
    if why_you_care:
        parts.append(f"<b>Why it matters:</b> {escape(why_you_care)}")
    parts.extend(["", f"Score: {float(decision.get('score') or 0):.2f}"])
    if tags:
        parts.append(tags)
    parts.extend(["", escape(action_url)])
    return "\n".join(parts)[:4000]


async def send_telegram(item: NewsItem, decision: dict[str, Any]) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    message = build_telegram_message(item, decision)
    async with Bot(settings.telegram_bot_token) as bot:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
    return True

