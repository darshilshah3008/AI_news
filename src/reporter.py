"""Report generator — formats fetched articles into a readable Markdown report."""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .fetcher import Article

logger = logging.getLogger(__name__)


def generate_report(articles: list[Article], save_dir: Optional[Path] = None) -> str:
    """Build a Markdown report grouped by category."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M UTC")

    # Group by category
    by_category: dict[str, list[Article]] = defaultdict(list)
    for a in articles:
        by_category[a.category].append(a)

    # Preferred category order
    order = ["Research", "Daily Summary", "Industry", "Developer"]
    sorted_categories = sorted(by_category.keys(), key=lambda c: order.index(c) if c in order else 99)

    lines = [
        f"# AI News Report — {date_str}",
        f"*Generated at {time_str} | {len(articles)} articles from {len(set(a.source for a in articles))} sources*\n",
        "---\n",
    ]

    for cat in sorted_categories:
        cat_articles = by_category[cat]
        emoji = {"Research": "🧠", "Daily Summary": "📰", "Industry": "🏢", "Developer": "💻"}.get(cat, "📌")
        lines.append(f"## {emoji} {cat}\n")

        # Group by source within category
        by_source: dict[str, list[Article]] = defaultdict(list)
        for a in cat_articles:
            by_source[a.source].append(a)

        for source_name, src_articles in by_source.items():
            lines.append(f"### {source_name}\n")
            for a in src_articles:
                pub = f" — _{a.published}_" if a.published else ""
                lines.append(f"- **{a.title}**{pub}")
                if a.summary:
                    lines.append(f"  > {a.summary}")
                lines.append(f"  [Read more]({a.url})")
                if a.tags:
                    lines.append(f"  Tags: {', '.join(a.tags[:5])}")
                lines.append("")
        lines.append("---\n")

    # Quick summary section
    lines.append("## 📊 Summary\n")
    lines.append(f"| Category | Articles | Sources |")
    lines.append(f"|---|---|---|")
    for cat in sorted_categories:
        cat_articles = by_category[cat]
        sources = set(a.source for a in cat_articles)
        lines.append(f"| {cat} | {len(cat_articles)} | {', '.join(sources)} |")
    lines.append("")

    report = "\n".join(lines)

    # Save to file if directory provided
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = save_dir / f"ai_news_{date_str}.md"
        filepath.write_text(report, encoding="utf-8")
        logger.info("Report saved to %s", filepath)

    return report
