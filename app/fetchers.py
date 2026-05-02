##Web Scraping & RSS Fetching Engine.
#The heavy lifter of the project. It uses `httpx` for async web requests, 
#`feedparser` to handle RSS feeds, and `BeautifulSoup4` to parse raw HTML pages.
#It includes semantic extraction logic to intelligently grab the context around 
#links so the AI has enough text to evaluate the opportunity.


from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.defaults import GENERIC_SECTION_TITLES
from app.models import NewsItem
from app.utils import build_item_id, clean_text, slugify


def is_generic_heading(title: str) -> bool:
    normalized = clean_text(title).lower()
    return not normalized or normalized in GENERIC_SECTION_TITLES


def build_news_item(
    *,
    source: str,
    title: str,
    url: str,
    text: str,
    published: str = "",
    company: str = "",
    category: str = "",
) -> NewsItem:
    normalized_title = clean_text(title) or "Untitled"
    normalized_url = url.strip()
    normalized_text = clean_text(text, settings.max_text_chars)
    return NewsItem(
        source=source,
        title=normalized_title,
        url=normalized_url,
        text=normalized_text,
        published=published,
        company=company,
        category=category,
        item_id=build_item_id(source, normalized_title, normalized_url),
    )


async def fetch_rss_items(client: httpx.AsyncClient, source: dict[str, Any]) -> list[NewsItem]:
    response = await client.get(source["url"])
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    items: list[NewsItem] = []
    limit = int(source.get("limit") or settings.max_items_per_source)
    for entry in parsed.entries:
        title = clean_text(entry.get("title", "Untitled"))
        link = entry.get("link") or entry.get("id") or ""
        if not link:
            continue
        summary = entry.get("summary") or entry.get("description") or title
        published = entry.get("published") or entry.get("updated") or ""
        items.append(
            build_news_item(
                source=source["name"],
                title=title,
                url=link,
                text=summary,
                published=published,
                company=str(source.get("company", "")),
                category=str(source.get("category", "rss")),
            )
        )
    return items[:limit]


def extract_semantic_items(
    soup: BeautifulSoup,
    *,
    source: str,
    page_url: str,
    company: str,
    category: str,
    limit: int,
) -> list[NewsItem]:
    root = soup.find("main") or soup.find("article") or soup.body or soup
    headings = root.find_all(["h1", "h2", "h3", "h4"])
    items: list[NewsItem] = []
    seen_titles: set[str] = set()

    for heading in headings:
        title = clean_text(heading.get_text(" ", strip=True))
        normalized_title = title.lower()
        if (
            not title
            or is_generic_heading(title)
            or normalized_title in seen_titles
            or len(title) < 4
            or len(title) > 140
        ):
            continue

        seen_titles.add(normalized_title)
        link_node = heading.find_parent("a", href=True) or heading.find_next("a", href=True)
        if link_node and link_node.get("href"):
            link = urljoin(page_url, link_node.get("href"))
        else:
            link = f"{page_url}#{slugify(title)}"

        context_parts: list[str] = []
        for sibling in heading.next_siblings:
            if getattr(sibling, "name", None) in {"h1", "h2", "h3", "h4"}:
                break
            sibling_text = clean_text(
                getattr(sibling, "get_text", lambda *args, **kwargs: str(sibling))(" ", strip=True)
            )
            if sibling_text:
                context_parts.append(sibling_text)
            if len(" ".join(context_parts)) > 1200 or len(context_parts) >= 4:
                break

        if not context_parts:
            parent_text = clean_text(heading.parent.get_text(" ", strip=True)) if heading.parent else ""
            if parent_text and parent_text != title:
                context_parts.append(parent_text)

        text = " ".join(part for part in context_parts if part)
        if not text:
            continue

        items.append(
            build_news_item(
                source=source,
                title=title,
                url=link,
                text=text,
                company=company,
                category=category,
            )
        )
        if len(items) >= limit:
            break

    return items


async def fetch_scraped_items(client: httpx.AsyncClient, target: dict[str, Any]) -> list[NewsItem]:
    url = str(target.get("url", "")).strip()
    if not url:
        return []

    response = await client.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    name = str(target.get("name") or url)
    company = str(target.get("company") or "")
    category = str(target.get("category") or "scraped page")
    item_selector = target.get("item_selector")
    title_selector = target.get("title_selector")
    link_selector = target.get("link_selector")
    summary_selector = target.get("summary_selector")
    limit = int(target.get("limit") or settings.max_items_per_source)

    if not item_selector:
        semantic_items = extract_semantic_items(
            soup,
            source=name,
            page_url=url,
            company=company,
            category=category,
            limit=limit,
        )
        if semantic_items:
            return semantic_items

        title = clean_text(soup.title.string if soup.title else name)
        main = soup.find("article") or soup.find("main") or soup.body or soup
        return [
            build_news_item(
                source=name,
                title=title,
                url=url,
                text=main.get_text(" ", strip=True),
                company=company,
                category=category,
            )
        ]

    items: list[NewsItem] = []
    for block in soup.select(str(item_selector))[:limit]:
        title_node = block.select_one(str(title_selector)) if title_selector else None
        title_node = title_node or block.find(["h1", "h2", "h3"])

        link_node = block.select_one(str(link_selector)) if link_selector else None
        link_node = link_node or block.find("a", href=True)

        summary_node = block.select_one(str(summary_selector)) if summary_selector else None
        link = link_node.get("href") if link_node else ""
        title = clean_text(title_node.get_text(" ", strip=True) if title_node else "")
        text_source = summary_node.get_text(" ", strip=True) if summary_node else block.get_text(" ", strip=True)

        if not title:
            title = clean_text(text_source, 120) or name
        if not link:
            link = f"{url}#{len(items) + 1}"

        items.append(
            build_news_item(
                source=name,
                title=title,
                url=urljoin(url, link),
                text=text_source,
                company=company,
                category=category,
            )
        )
    return items


async def gather_items() -> tuple[list[NewsItem], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    items: list[NewsItem] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AI-News-Automation/1.0; "
            "+https://render.com)"
        )
    }
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        tasks: list[tuple[str, asyncio.Task[list[NewsItem]]]] = []
        for source in settings.rss_sources:
            tasks.append((source["name"], asyncio.create_task(fetch_rss_items(client, source))))
        for target in settings.scrape_targets:
            source_name = str(target.get("name") or target.get("url") or "Scrape target")
            tasks.append((source_name, asyncio.create_task(fetch_scraped_items(client, target))))

        for name, task in tasks:
            try:
                items.extend(await task)
            except Exception as exc:  # noqa: BLE001 - capture source-level failures for API output.
                errors.append({"source": name, "error": str(exc)})

    deduped: dict[str, NewsItem] = {}
    for item in items:
        key = item.item_id or build_item_id(item.source, item.title, item.url)
        if key not in deduped:
            deduped[key] = item
    return list(deduped.values()), errors

