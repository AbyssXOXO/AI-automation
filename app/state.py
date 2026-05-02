##Persistent Memory Manager.
#Responsible for ensuring the bot doesn't spam you with duplicate alerts. 
#It manages reading and writing to a local `state.json` file, acting as a 
#rolling cache (up to the configured maximum limit) of the unique fingerprints 
#for every opportunity the bot has already processed.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


class StateStore:
    def __init__(self, path: Path, max_seen: int) -> None:
        self.path = path
        self.max_seen = max_seen
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"seen_items": [], "last_scan_at": None, "last_results": []}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            data = {}
        if "seen_items" not in data and "seen_links" in data:
            data["seen_items"] = data.get("seen_links", [])
        data.setdefault("seen_items", [])
        data.setdefault("last_scan_at", None)
        data.setdefault("last_results", [])
        return data

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)

    @property
    def seen_items(self) -> set[str]:
        return set(self.data.get("seen_items", []))

    def mark_seen(self, item_ids: list[str]) -> None:
        existing = set(self.data.get("seen_items", []))
        ordered = list(self.data.get("seen_items", []))
        for item_id in item_ids:
            if item_id and item_id not in existing:
                ordered.append(item_id)
                existing.add(item_id)
        self.data["seen_items"] = ordered[-self.max_seen :]

    def set_last_scan(self, result: dict[str, Any]) -> None:
        self.data["last_scan_at"] = result["finished_at"]
        self.data["last_results"] = result.get("notifications", [])[:20]
        self.save()


state = StateStore(settings.state_file, settings.max_seen_items)

