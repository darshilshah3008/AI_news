from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from . import db
from .models import ProjectProfile
from .parser import parse_report
from .scoring import decode_project, score_article


def ingest_file(path: Path) -> int:
    records = parse_report(path)
    seen: set[str] = set()
    count = 0
    for r in records:
        if r.dedupe_key in seen:
            continue
        seen.add(r.dedupe_key)
        db.upsert_article(r)
        count += 1
    return count


def ingest_dir(path: Path) -> int:
    total = 0
    for md in sorted(path.glob("*.md")):
        total += ingest_file(md)
    return total


def seed_projects() -> None:
    samples = [
        ProjectProfile(
            name="Orin Nano Edge Assistant",
            description="On-device multimodal assistant for field technicians running on NVIDIA Orin Nano.",
            hardware_target="NVIDIA Orin Nano",
            deployment_style="edge/local",
            offline_requirement="high",
            latency_sensitivity="high",
            power_sensitivity="medium",
            memory_constraints="8GB",
            preferred_frameworks=["TensorRT", "ONNX Runtime", "CUDA"],
            excluded_technologies=["cloud-only"],
            categories_of_interest=["Research", "Developer"],
            goals="Ship low-latency assistant with local inference and vision/audio support.",
            evaluation_priorities="latency, memory footprint, quantization quality",
        ),
        ProjectProfile(
            name="Document AI Startup",
            description="Document extraction + retrieval product for regulated industries.",
            hardware_target="x86 CPU + optional GPU",
            deployment_style="hybrid",
            offline_requirement="medium",
            latency_sensitivity="medium",
            power_sensitivity="low",
            memory_constraints="16GB",
            preferred_frameworks=["PyTorch", "Transformers", "OCR"],
            excluded_technologies=["consumer-only"],
            categories_of_interest=["Research", "Industry", "Developer"],
            goals="Improve extraction accuracy and RAG quality.",
            evaluation_priorities="accuracy, compliance, cost",
        ),
        ProjectProfile(
            name="AI SaaS Copilot",
            description="B2B SaaS assistant that automates support and operations workflows.",
            hardware_target="cloud",
            deployment_style="SaaS",
            offline_requirement="low",
            latency_sensitivity="medium",
            power_sensitivity="low",
            memory_constraints="N/A",
            preferred_frameworks=["FastAPI", "LangGraph", "OpenAPI"],
            excluded_technologies=["edge-only"],
            categories_of_interest=["Industry", "Developer"],
            goals="Increase workflow automation coverage and reliability.",
            evaluation_priorities="integration speed, reliability, ROI",
        ),
    ]
    for p in samples:
        db.save_project(p)


def get_recommendations(project_id: int, limit: int = 50) -> list[dict]:
    project_row = db.get_project(project_id)
    if not project_row:
        return []
    project = decode_project(project_row)
    recs = []
    for article in db.list_articles()[:200]:
        rec = score_article(dict(article), project)
        combined = dict(article)
        combined.update({
            "importance_score": rec.importance_score,
            "relevance_score": rec.relevance_score,
            "confidence_score": rec.confidence_score,
            "action": rec.action,
            "reasoning": rec.reasoning,
        })
        recs.append(combined)
    recs.sort(key=lambda x: (x["relevance_score"], x["importance_score"]), reverse=True)
    return recs[:limit]


def build_weekly_brief(project_id: int) -> str:
    recs = get_recommendations(project_id, limit=30)
    project = db.get_project(project_id)
    if not project:
        return "Project not found"
    top = recs[:8]
    action_counts = Counter(r["action"] for r in recs)
    test_candidates = [r for r in recs if r["action"] in {"BUILD", "TEST"}][:5]
    ignore = [r for r in recs if r["action"] == "IGNORE"][:5]

    lines = [
        f"# AI Signal OS Weekly Brief — {project['name']}",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Executive Summary",
        f"This week surfaced {len(recs)} relevant signals. Prioritize {action_counts.get('BUILD',0)} BUILD items and {action_counts.get('TEST',0)} TEST experiments.",
        "",
        "## Top Relevant Developments",
    ]
    for r in top:
        lines.append(f"- **{r['title']}** ({r['source']}) — {r['action']} | relevance {r['relevance_score']}")
        lines.append(f"  - Why: {r['reasoning']}")

    lines += ["", "## Best-Fit Models/Tools/Frameworks to Test"]
    for r in test_candidates:
        lines.append(f"- {r['title']} ({r['url']})")

    lines += ["", "## Suggested Architecture Direction", "- Favor modular pipelines with measurable latency and memory budgets.", "- Keep optional cloud fallback; preserve local-first path for critical workflows."]
    lines += ["", "## Prototype Next Steps", "- Build 2 rapid experiments from BUILD signals.", "- Convert 3 TEST signals into benchmark tasks.", "- Add instrumentation for quality, latency, and cost."]
    lines += ["", "## What to Ignore", *(f"- {r['title']}" for r in ignore)]
    lines += ["", "## Risks / Open Questions", "- Which model updates materially improve quality on your own eval set?", "- Are infra-only announcements creating lock-in risk?"]

    return "\n".join(lines)


def export_markdown(content: str, filename: str) -> Path:
    out_dir = Path("data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def build_timeline(project_id: int) -> str:
    recs = get_recommendations(project_id, limit=120)
    by_date: dict[str, list[dict]] = {}
    for r in recs:
        date = r.get("report_date") or "unknown"
        by_date.setdefault(date, []).append(r)

    lines = ["# AI Signal OS Timeline", ""]
    for day in sorted(by_date.keys(), reverse=True):
        lines.append(f"## {day}")
        for r in sorted(by_date[day], key=lambda x: x["relevance_score"], reverse=True)[:6]:
            lines.append(f"- [{r['action']}] {r['title']} ({r['source']}) — relevance {r['relevance_score']}")
        lines.append("")
    return "\n".join(lines)
