from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def parse_named_urls(raw: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for index, chunk in enumerate(raw.split(","), start=1):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            name, url = chunk.split("=", 1)
            sources.append({"name": name.strip() or f"RSS {index}", "url": url.strip()})
        else:
            sources.append({"name": f"RSS {index}", "url": chunk})
    return [source for source in sources if source["url"]]


def parse_json_list(name: str) -> list[dict[str, Any]]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "item"


def build_item_id(*parts: str) -> str:
    payload = "|".join(part.strip() for part in parts if part and part.strip())
    if not payload:
        payload = iso_now()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def clean_text(value: str, max_chars: int | None = None) -> str:
    soup = BeautifulSoup(value or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars and len(text) > max_chars:
        return text[: max_chars - 3].rstrip() + "..."
    return text


def parse_model_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response was not a JSON object")
    return parsed

