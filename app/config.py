##Configuration Management.
#This module handles all the environment variables and settings for the bot.
#It defines the default behaviors, scraping limits, and AI parameters. 
#If someone forks this repo, this is the central place to see all the 
#"knobs and dials" they can tweak via their .env file.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.defaults import DEFAULT_BIG_TECH_SCRAPE_TARGETS
from app.utils import env_bool, env_float, env_int, parse_json_list, parse_named_urls


@dataclass(slots=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_ACCOUNT_ID", "")
    target_companies: str = os.getenv("TARGET_COMPANIES", "Google, Microsoft, IBM")
    user_profile: str = os.getenv(
        "USER_PROFILE",
        "Student/builder interested in Python, AI, cloud, developer tools, free courses, "
        "hackathons, and career-building opportunities.",
    )
    topic_prompt: str = os.getenv(
        "TOPIC_PROMPT",
        "Free courses, hackathons, coding challenges, student programs, developer events, "
        "certification offers, and hands-on AI or cloud opportunities from Google, Microsoft, "
        "and IBM.",
    )
    relevance_threshold: float = env_float("RELEVANCE_THRESHOLD", 0.7)
    gemini_request_delay: float = env_float("GEMINI_REQUEST_DELAY", 4.5) 
    scan_interval_minutes: int = env_int("SCAN_INTERVAL_MINUTES", 180)
    startup_scan: bool = env_bool("RUN_SCAN_ON_STARTUP", False)
    background_loop: bool = env_bool("RUN_BACKGROUND_LOOP", True)
    max_items_per_scan: int = env_int("MAX_ITEMS_PER_SCAN", 25)
    max_items_per_source: int = env_int("MAX_ITEMS_PER_SOURCE", 8)
    max_text_chars: int = env_int("MAX_TEXT_CHARS", 5000)
    max_seen_items: int = env_int("MAX_SEEN_ITEMS", 2000)
    state_file: Path = Path(os.getenv("STATE_FILE", "state.json"))
    request_timeout_seconds: float = env_float("REQUEST_TIMEOUT_SECONDS", 20.0)

    @property
    def rss_sources(self) -> list[dict[str, Any]]:
        raw = os.getenv("RSS_FEEDS", "")
        return parse_named_urls(raw)

    @property
    def scrape_targets(self) -> list[dict[str, Any]]:
        targets = parse_json_list("SCRAPE_TARGETS")
        if targets:
            return targets
        return DEFAULT_BIG_TECH_SCRAPE_TARGETS


settings = Settings()

