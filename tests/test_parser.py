from pathlib import Path

from aisignal.parser import parse_report


def test_parse_report_extracts_articles():
    items = parse_report(Path("reports/ai_news_2026-04-13.md"))
    assert len(items) > 10
    first = items[0]
    assert first.title
    assert first.url.startswith("http")
    assert first.report_date == "2026-04-13"
