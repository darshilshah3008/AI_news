from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ArticleRecord, ProjectProfile


DB_PATH = Path("data/ai_signal_os.db")


def get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT,
                category TEXT,
                source TEXT,
                title TEXT,
                published_date TEXT,
                summary TEXT,
                tags TEXT,
                url TEXT UNIQUE,
                modality TEXT,
                deployment_fit TEXT,
                entities TEXT,
                dedupe_key TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                hardware_target TEXT,
                deployment_style TEXT,
                offline_requirement TEXT,
                latency_sensitivity TEXT,
                power_sensitivity TEXT,
                memory_constraints TEXT,
                preferred_frameworks TEXT,
                excluded_technologies TEXT,
                categories_of_interest TEXT,
                goals TEXT,
                evaluation_priorities TEXT
            );
            """
        )


def upsert_article(article: ArticleRecord, db_path: Path | None = None) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO articles (
                report_date, category, source, title, published_date, summary,
                tags, url, modality, deployment_fit, entities, dedupe_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                summary=excluded.summary,
                tags=excluded.tags,
                title=excluded.title,
                report_date=excluded.report_date,
                category=excluded.category,
                source=excluded.source,
                published_date=excluded.published_date,
                modality=excluded.modality,
                deployment_fit=excluded.deployment_fit,
                entities=excluded.entities,
                dedupe_key=excluded.dedupe_key
            """,
            (
                article.report_date,
                article.category,
                article.source,
                article.title,
                article.published_date,
                article.summary,
                json.dumps(article.tags),
                article.url,
                article.modality,
                article.deployment_fit,
                json.dumps(article.entities),
                article.dedupe_key,
            ),
        )


def list_articles(db_path: Path | None = None) -> list[sqlite3.Row]:
    with get_conn(db_path) as conn:
        return conn.execute(
            "SELECT * FROM articles ORDER BY report_date DESC, id DESC"
        ).fetchall()


def save_project(profile: ProjectProfile, db_path: Path | None = None) -> int:
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO projects (
                name, description, hardware_target, deployment_style, offline_requirement,
                latency_sensitivity, power_sensitivity, memory_constraints,
                preferred_frameworks, excluded_technologies, categories_of_interest,
                goals, evaluation_priorities
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description=excluded.description,
                hardware_target=excluded.hardware_target,
                deployment_style=excluded.deployment_style,
                offline_requirement=excluded.offline_requirement,
                latency_sensitivity=excluded.latency_sensitivity,
                power_sensitivity=excluded.power_sensitivity,
                memory_constraints=excluded.memory_constraints,
                preferred_frameworks=excluded.preferred_frameworks,
                excluded_technologies=excluded.excluded_technologies,
                categories_of_interest=excluded.categories_of_interest,
                goals=excluded.goals,
                evaluation_priorities=excluded.evaluation_priorities
            """,
            (
                profile.name,
                profile.description,
                profile.hardware_target,
                profile.deployment_style,
                profile.offline_requirement,
                profile.latency_sensitivity,
                profile.power_sensitivity,
                profile.memory_constraints,
                json.dumps(profile.preferred_frameworks),
                json.dumps(profile.excluded_technologies),
                json.dumps(profile.categories_of_interest),
                profile.goals,
                profile.evaluation_priorities,
            ),
        )
        row = conn.execute("SELECT id FROM projects WHERE name = ?", (profile.name,)).fetchone()
        return int(row["id"])


def get_projects(db_path: Path | None = None) -> list[sqlite3.Row]:
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()


def get_project(project_id: int, db_path: Path | None = None) -> sqlite3.Row | None:
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
