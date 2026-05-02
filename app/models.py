##Data Models.
#Defines the core data structures used throughout the application. 
#The `NewsItem` dataclass acts as the standard blueprint for an opportunity 
#as it travels through the pipeline: from the scraper, to the AI gatekeeper, 
#and finally out to Telegram.

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

