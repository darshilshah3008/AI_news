"""AI Signal OS CLI and ingestion utility."""

from __future__ import annotations

import argparse
from pathlib import Path

from .aisignal import db
from .aisignal.services import (
    build_timeline,
    build_weekly_brief,
    export_markdown,
    get_recommendations,
    ingest_dir,
    ingest_file,
    seed_projects,
)
from .aisignal.web import run_server


def cmd_init_db(_: argparse.Namespace) -> None:
    db.init_db()
    seed_projects()
    print("Initialized database and sample projects.")


def cmd_ingest_file(args: argparse.Namespace) -> None:
    db.init_db()
    n = ingest_file(Path(args.path))
    print(f"Ingested {n} articles from {args.path}")


def cmd_ingest_dir(args: argparse.Namespace) -> None:
    db.init_db()
    n = ingest_dir(Path(args.path))
    print(f"Ingested {n} articles from directory {args.path}")


def cmd_list_articles(_: argparse.Namespace) -> None:
    rows = db.list_articles()
    for r in rows[:100]:
        print(f"[{r['id']}] {r['report_date']} | {r['category']} | {r['title']}")
    print(f"Total: {len(rows)}")


def cmd_recommend(args: argparse.Namespace) -> None:
    recs = get_recommendations(args.project_id, limit=args.limit)
    for r in recs:
        print(f"[{r['action']}] rel={r['relevance_score']} imp={r['importance_score']} :: {r['title']}")


def cmd_export_timeline(args: argparse.Namespace) -> None:
    content = build_timeline(args.project_id)
    path = export_markdown(content, f"project_{args.project_id}_timeline.md")
    print(path)


def cmd_export_project(args: argparse.Namespace) -> None:
    content = build_weekly_brief(args.project_id)
    path = export_markdown(content, f"project_{args.project_id}_brief.md")
    print(path)


def cmd_runserver(args: argparse.Namespace) -> None:
    run_server(host=args.host, port=args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m AI_news", description="AI Signal OS")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="Initialize SQLite DB and sample projects")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("ingest-file", help="Ingest one markdown report")
    p.add_argument("path")
    p.set_defaults(func=cmd_ingest_file)

    p = sub.add_parser("ingest-dir", help="Ingest all markdown reports from directory")
    p.add_argument("path", default="reports", nargs="?")
    p.set_defaults(func=cmd_ingest_dir)

    p = sub.add_parser("list-articles", help="List ingested article records")
    p.set_defaults(func=cmd_list_articles)

    p = sub.add_parser("recommend", help="Generate recommendations for a project")
    p.add_argument("project_id", type=int)
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("export-timeline", help="Export project timeline markdown")
    p.add_argument("project_id", type=int)
    p.set_defaults(func=cmd_export_timeline)

    p = sub.add_parser("export-project", help="Export project weekly brief markdown")
    p.add_argument("project_id", type=int)
    p.set_defaults(func=cmd_export_project)

    p = sub.add_parser("runserver", help="Run web app locally")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_runserver)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
