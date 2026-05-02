from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NewsItem:
    source: str
    title: str
    url: str
    text: str
    published: str = ""
    company: str = ""
    category: str = ""
    item_id: str = ""

