"""AI news source definitions.

Each source has a name, category, URL, and optional RSS feed URL.
RSS feeds are preferred for reliability; HTML fallback uses BeautifulSoup.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsSource:
    name: str
    category: str
    url: str
    rss_url: Optional[str] = None
    css_selector: Optional[str] = None  # fallback for HTML scraping


# ── Research & Breakthroughs ──────────────────────────────────────────
RESEARCH_SOURCES = [
    NewsSource(
        name="MIT AI News",
        category="Research",
        url="https://news.mit.edu/topic/artificial-intelligence2",
        rss_url="https://news.mit.edu/topic/artificial-intelligence2/feed",
    ),
    NewsSource(
        name="OpenAI Blog",
        category="Research",
        url="https://openai.com/blog",
        rss_url="https://openai.com/blog/rss.xml",
    ),
    NewsSource(
        name="Google DeepMind Blog",
        category="Research",
        url="https://deepmind.google/discover/blog/",
        rss_url="https://deepmind.google/blog/rss.xml",
    ),
    NewsSource(
        name="Hugging Face Blog",
        category="Research",
        url="https://huggingface.co/blog",
        rss_url="https://huggingface.co/blog/feed.xml",
    ),
    NewsSource(
        name="Berkeley AI Research (BAIR)",
        category="Research",
        url="https://bair.berkeley.edu/blog/",
        rss_url="https://bair.berkeley.edu/blog/feed.xml",
    ),
]

# ── Daily Summaries & Newsletters ─────────────────────────────────────
DAILY_SOURCES = [
    NewsSource(
        name="The Rundown AI",
        category="Daily Summary",
        url="https://www.therundown.ai/",
    ),
    NewsSource(
        name="Ben's Bites",
        category="Daily Summary",
        url="https://bensbites.beehiiv.com/",
    ),
]

# ── Industry & Business ──────────────────────────────────────────────
INDUSTRY_SOURCES = [
    NewsSource(
        name="Reuters AI",
        category="Industry",
        url="https://www.reuters.com/technology/artificial-intelligence/",
    ),
    NewsSource(
        name="TechCrunch AI",
        category="Industry",
        url="https://techcrunch.com/category/artificial-intelligence/",
        rss_url="https://techcrunch.com/category/artificial-intelligence/feed/",
    ),
    NewsSource(
        name="VentureBeat AI",
        category="Industry",
        url="https://venturebeat.com/category/ai/",
        rss_url="https://venturebeat.com/category/ai/feed/",
    ),
    NewsSource(
        name="Ars Technica AI",
        category="Industry",
        url="https://arstechnica.com/ai-policy/",
        rss_url="https://feeds.arstechnica.com/arstechnica/technology-lab",
    ),
]

# ── Developer & Technical ────────────────────────────────────────────
DEVELOPER_SOURCES = [
    NewsSource(
        name="KDnuggets",
        category="Developer",
        url="https://www.kdnuggets.com/",
        rss_url="https://www.kdnuggets.com/feed",
    ),
    NewsSource(
        name="Towards Data Science",
        category="Developer",
        url="https://towardsdatascience.com/",
    ),
    NewsSource(
        name="Analytics Vidhya",
        category="Developer",
        url="https://www.analyticsvidhya.com/blog/",
        rss_url="https://feeds.feedburner.com/AnalyticsVidhya",
    ),
]

# ── All sources combined ─────────────────────────────────────────────
ALL_SOURCES = RESEARCH_SOURCES + DAILY_SOURCES + INDUSTRY_SOURCES + DEVELOPER_SOURCES
