"""AI News Agent — CLI entry point.

Usage:
    python -m AI_news                    Fetch all AI news and display report
    python -m AI_news --save             Fetch and save report to reports/ folder
    python -m AI_news --category research  Filter by category (research/daily/industry/developer)
    python -m AI_news --items 10         Max articles per source (default: 5)
"""

import argparse
import logging
import sys
from pathlib import Path

from .src.fetcher import fetch_all
from .src.reporter import generate_report
from .src.sources import (
    ALL_SOURCES,
    RESEARCH_SOURCES,
    DAILY_SOURCES,
    INDUSTRY_SOURCES,
    DEVELOPER_SOURCES,
)

CATEGORY_MAP = {
    "research": RESEARCH_SOURCES,
    "daily": DAILY_SOURCES,
    "industry": INDUSTRY_SOURCES,
    "developer": DEVELOPER_SOURCES,
    "all": ALL_SOURCES,
}

REPORTS_DIR = Path(__file__).parent / "reports"


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI News Agent — Fetch and summarize AI news from top sources",
        prog="python -m AI_news",
    )
    parser.add_argument(
        "--category", "-c",
        choices=list(CATEGORY_MAP.keys()),
        default="all",
        help="Filter by category (default: all)",
    )
    parser.add_argument(
        "--items", "-n",
        type=int,
        default=5,
        help="Max articles per source (default: 5)",
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save report to AI_news/reports/ folder",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    sources = CATEGORY_MAP[args.category]
    print(f"Fetching AI news from {len(sources)} sources...\n")

    articles = fetch_all(sources=sources, max_items=args.items)

    if not articles:
        print("No articles fetched. Check your internet connection or try again.")
        sys.exit(1)

    save_dir = REPORTS_DIR if args.save else None
    report = generate_report(articles, save_dir=save_dir)
    print(report)

    if args.save:
        print(f"\nReport saved to {REPORTS_DIR}/")


if __name__ == "__main__":
    main()
