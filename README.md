# AI News Agent

A standalone Python agent that fetches and summarizes AI news from top research labs, industry outlets, newsletters, and developer blogs — delivering a concise Markdown report.

## What It Does

- **Fetches news** from 14 curated AI sources (RSS + HTML fallback)
- **Categorizes articles** into Research, Daily Summary, Industry, and Developer
- **Generates Markdown reports** grouped by category and source
- **Saves reports** to `reports/` for historical reference
- **Runs in parallel** for fast fetching across all sources

## Sources

| Category | Sources |
|---|---|
| **Research** | MIT AI News, OpenAI Blog, Google DeepMind Blog, Hugging Face Blog, Berkeley AI Research (BAIR) |
| **Daily Summary** | The Rundown AI, Ben's Bites |
| **Industry** | Reuters AI, TechCrunch AI, VentureBeat AI, Ars Technica AI |
| **Developer** | KDnuggets, Towards Data Science, Analytics Vidhya |

Sources are defined in `src/sources.py` and can be easily extended.

## Quick Start

### 1. Install

```bash
cd AI_news
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

### 2. Run

```bash
# Fetch all AI news
python -m AI_news

# Fetch and save report to reports/ folder
python -m AI_news --save

# Filter by category
python -m AI_news -c research       # Research only
python -m AI_news -c industry       # Industry/business
python -m AI_news -c daily          # Daily summaries
python -m AI_news -c developer      # Developer/technical

# Control articles per source (default: 5)
python -m AI_news -n 10

# Combine options
python -m AI_news -c research -n 10 --save

# Verbose logging
python -m AI_news -v
```

## CLI Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--category` | `-c` | Filter: `all`, `research`, `daily`, `industry`, `developer` | `all` |
| `--items` | `-n` | Max articles per source | `5` |
| `--save` | `-s` | Save report to `reports/` folder | off |
| `--verbose` | `-v` | Enable debug logging | off |

## Report Output

Reports are generated as Markdown, printed to the terminal, and optionally saved to `reports/ai_news_YYYY-MM-DD.md`.

### Example Output

```
# AI News Report — 2026-04-02
*Generated at 15:50 UTC | 45 articles from 9 sources*

---

## 🧠 Research

### OpenAI Blog

- **Accelerating the next phase of AI** — _Tue, 31 Mar 2026_
  > OpenAI raises $122 billion in new funding to expand frontier AI globally.
  [Read more](https://openai.com/index/accelerating-the-next-phase-ai)

### Google DeepMind Blog

- **Measuring progress toward AGI: A cognitive framework** — _Tue, 17 Mar 2026_
  > Introducing a framework to measure progress toward AGI.
  [Read more](https://deepmind.google/blog/measuring-progress-toward-agi/)

## 🏢 Industry

### TechCrunch AI
...
```

## Project Structure

```
AI_news/
├── __init__.py
├── __main__.py          # CLI entry point
├── requirements.txt     # Dependencies
├── README.md
├── reports/             # Saved reports (auto-created)
└── src/
    ├── __init__.py
    ├── sources.py       # News source definitions (14 sources)
    ├── fetcher.py       # RSS parser + HTML scraper (parallel)
    └── reporter.py      # Markdown report generator
```

## Adding New Sources

Edit `src/sources.py` and add a `NewsSource` to the appropriate list:

```python
NewsSource(
    name="Your Source Name",
    category="Research",           # Research | Daily Summary | Industry | Developer
    url="https://example.com/ai",
    rss_url="https://example.com/ai/feed.xml",  # optional, preferred
)
```

RSS feeds are tried first for reliability. If no RSS is available, the fetcher falls back to HTML scraping of headlines.

## Dependencies

- `requests` — HTTP client
- `beautifulsoup4` — HTML parsing
- `feedparser` — RSS/Atom feed parsing

## Making It Standalone

To use this as a standalone project outside of AI_Repo:

```bash
# Copy the AI_news folder
cp -r AI_news /path/to/new/location

# Initialize a new git repo
cd /path/to/new/location/AI_news
git init
git add .
git commit -m "Initial commit: AI News Agent"

# Set up and run
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m AI_news --save
```

No external configuration or environment variables required — it works out of the box.
