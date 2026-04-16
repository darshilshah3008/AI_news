"""Fetcher module — retrieves articles from RSS feeds and web pages."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import requests
from bs4 import BeautifulSoup

from .sources import NewsSource, ALL_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 15


@dataclass
class Article:
    title: str
    source: str
    category: str
    url: str
    summary: str = ""
    published: Optional[str] = None
    tags: list[str] = field(default_factory=list)


def _clean_html(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = BeautifulSoup(raw, "html.parser").get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def fetch_rss(source: NewsSource, max_items: int = 5) -> list[Article]:
    """Parse an RSS/Atom feed and return articles."""
    if not source.rss_url:
        return []
    try:
        feed = feedparser.parse(source.rss_url)
        articles = []
        for entry in feed.entries[:max_items]:
            summary_raw = entry.get("summary", "") or entry.get("description", "")
            published = entry.get("published", entry.get("updated", ""))
            tags = [t.get("term", "") for t in entry.get("tags", [])]
            articles.append(Article(
                title=entry.get("title", "Untitled"),
                source=source.name,
                category=source.category,
                url=entry.get("link", source.url),
                summary=_truncate(_clean_html(summary_raw)),
                published=published,
                tags=tags,
            ))
        logger.info("RSS: %s — %d articles", source.name, len(articles))
        return articles
    except Exception as exc:
        logger.warning("RSS failed for %s: %s", source.name, exc)
        return []


def fetch_html(source: NewsSource, max_items: int = 5) -> list[Article]:
    """Scrape headlines from a web page (fallback when no RSS)."""
    try:
        resp = requests.get(source.url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = []
        # Try common patterns for article links
        seen_titles: set[str] = set()
        for tag in soup.find_all(["h2", "h3", "h4", "article"]):
            link = tag.find("a") if tag.name != "a" else tag
            if not link or not link.get("href"):
                # Try the tag itself if it's inside an <a>
                parent_a = tag.find_parent("a")
                if parent_a and parent_a.get("href"):
                    link = parent_a
                else:
                    continue

            title = link.get_text(strip=True)
            href = link["href"]
            if not title or len(title) < 10 or title in seen_titles:
                continue
            seen_titles.add(title)

            # Make relative URLs absolute
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(source.url, href)

            articles.append(Article(
                title=_truncate(title, 200),
                source=source.name,
                category=source.category,
                url=href,
            ))
            if len(articles) >= max_items:
                break

        logger.info("HTML: %s — %d articles", source.name, len(articles))
        return articles
    except Exception as exc:
        logger.warning("HTML scrape failed for %s: %s", source.name, exc)
        return []


def fetch_source(source: NewsSource, max_items: int = 5) -> list[Article]:
    """Fetch articles from a source, trying RSS first then HTML fallback."""
    articles = fetch_rss(source, max_items)
    if not articles:
        articles = fetch_html(source, max_items)
    return articles


def fetch_all(sources: list[NewsSource] | None = None, max_items: int = 5,
              max_workers: int = 8) -> list[Article]:
    """Fetch articles from all sources in parallel."""
    sources = sources or ALL_SOURCES
    all_articles: list[Article] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_source, s, max_items): s for s in sources}
        for future in as_completed(futures):
            source = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as exc:
                logger.warning("Failed to fetch %s: %s", source.name, exc)

    logger.info("Total articles fetched: %d from %d sources", len(all_articles), len(sources))
    return all_articles
