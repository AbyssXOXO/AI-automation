from __future__ import annotations

import asyncio
from typing import Any

import google.generativeai as genai

from app.config import settings
from app.models import NewsItem
from app.utils import parse_model_json


def build_gatekeeper_prompt(item: NewsItem) -> str:
    return f"""
You are an AI gatekeeper for Telegram news alerts.

Target companies:
{settings.target_companies}

Alert topic:
{settings.topic_prompt}

User profile:
{settings.user_profile}

Evaluate whether this item deserves a notification. Prefer concrete, current,
actionable opportunities like free courses, hackathons, coding challenges,
student programs, free certification offers, vouchers, and registration-open
developer events from the target companies.

Strong positives:
- free or clearly student-friendly
- AI, Python, cloud, software engineering, Gemini, Azure, watsonx, or related skills
- hackathons, challenges, codelabs, training programs, certifications, vouchers
- explicit calls to register, learn, earn a badge, win, or apply

Strong negatives:
- generic docs or product pages with no specific opportunity
- paid-only training
- stale or past events that are already over
- duplicate or weakly relevant announcements
- vague marketing with no clear action for the user

Return only a JSON object with these exact keys:
{{
  "relevant": true,
  "score": 0.0,
  "company": "Google",
  "opportunity_type": "hackathon",
  "title": "Official opportunity title",
  "summary": "One concise sentence for Telegram.",
  "why_you_care": "One sentence explaining why this matches the user.",
  "deadline": "Unknown",
  "prize": "Unknown",
  "cost": "Free",
  "action_url": "https://example.com",
  "reason": "Why this should or should not be sent.",
  "tags": ["short", "tags"]
}}

Use score from 0.0 to 1.0. Set relevant to true only when score is at least
{settings.relevance_threshold}.

If a date appears to be clearly in the past and the opportunity is not ongoing
or self-paced, set relevant to false. Use "Unknown" when a field is missing.

Item:
Source: {item.source}
Company hint: {item.company or "unknown"}
Category hint: {item.category or "unknown"}
Title: {item.title}
URL: {item.url}
Published: {item.published or "unknown"}
Text: {item.text[: settings.max_text_chars]}
""".strip()


async def evaluate_with_gemini(item: NewsItem) -> dict[str, Any]:
    if not settings.gemini_api_key:
        return {
            "relevant": False,
            "score": 0.0,
            "summary": "",
            "reason": "GEMINI_API_KEY or API_KEY is not configured.",
            "tags": [],
        }

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = build_gatekeeper_prompt(item)

    def run_model() -> str:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        )
        return response.text or "{}"

    raw = await asyncio.to_thread(run_model)
    parsed = parse_model_json(raw)
    score = float(parsed.get("score") or 0.0)
    parsed["score"] = max(0.0, min(1.0, score))
    parsed["relevant"] = bool(parsed.get("relevant")) and parsed["score"] >= settings.relevance_threshold
    parsed.setdefault("company", item.company or "")
    parsed.setdefault("opportunity_type", item.category or "opportunity")
    parsed.setdefault("title", item.title)
    parsed.setdefault("summary", "")
    parsed.setdefault("why_you_care", "")
    parsed.setdefault("deadline", "Unknown")
    parsed.setdefault("prize", "Unknown")
    parsed.setdefault("cost", "Unknown")
    parsed.setdefault("action_url", item.url)
    parsed.setdefault("reason", "")
    parsed.setdefault("tags", [])
    if not isinstance(parsed["tags"], list):
        parsed["tags"] = []
    return parsed

