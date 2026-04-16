from __future__ import annotations

import json
from dataclasses import asdict

from .models import ProjectProfile, Recommendation

ACTIONS = ["BUILD", "TEST", "LEARN", "WATCH", "IGNORE"]


def _score_terms(text: str, terms: list[str], weight: float) -> float:
    low = text.lower()
    return sum(weight for t in terms if t.lower() in low)


def score_article(article: dict, project: ProjectProfile) -> Recommendation:
    text = " ".join([
        article.get("title", ""),
        article.get("summary", ""),
        article.get("category", ""),
        article.get("deployment_fit", ""),
        article.get("modality", ""),
    ])

    importance = 35.0
    relevance = 20.0
    confidence = 0.65
    reasons: list[str] = []

    edge_terms = ["edge", "on-device", "jetson", "orin", "quantization", "onnx", "tensorrt", "cuda", "real-time", "efficient"]
    doc_terms = ["document", "ocr", "rag", "embedding", "retrieval", "pdf"]
    saas_terms = ["assistant", "copilot", "workflow", "agent", "api", "integration"]
    low_value_terms = ["funding", "raises", "acquires", "lawsuit", "conference"]

    importance += _score_terms(text, ["launch", "new", "release", "benchmark", "open model"], 7)
    importance += _score_terms(text, ["security", "breaking", "vulnerability"], 6)
    importance -= _score_terms(text, low_value_terms, 6)

    proj_text = " ".join([
        project.name,
        project.description,
        project.hardware_target,
        project.deployment_style,
        project.goals,
        project.evaluation_priorities,
        " ".join(project.preferred_frameworks),
        " ".join(project.categories_of_interest),
    ]).lower()

    if "orin" in proj_text or "jetson" in proj_text or "edge" in proj_text:
        v = _score_terms(text, edge_terms, 10)
        relevance += v
        if v:
            reasons.append("Matches edge/on-device deployment constraints")
    if "document" in proj_text or "ocr" in proj_text:
        v = _score_terms(text, doc_terms, 9)
        relevance += v
        if v:
            reasons.append("Useful for document understanding workflow")
    if "saas" in proj_text or "copilot" in proj_text:
        v = _score_terms(text, saas_terms, 8)
        relevance += v
        if v:
            reasons.append("Aligned with SaaS assistant roadmap")

    for blocked in project.excluded_technologies:
        if blocked.lower() in text.lower():
            relevance -= 20
            reasons.append(f"Contains excluded technology: {blocked}")

    if article.get("deployment_fit") == "edge":
        relevance += 12
    if article.get("modality") == "multimodal" and "multimodal" in proj_text:
        relevance += 8

    importance = max(0, min(100, importance))
    relevance = max(0, min(100, relevance))

    total = (importance * 0.45) + (relevance * 0.55)
    if total >= 78:
        action = "BUILD"
    elif total >= 62:
        action = "TEST"
    elif total >= 48:
        action = "LEARN"
    elif total >= 35:
        action = "WATCH"
    else:
        action = "IGNORE"

    if not reasons:
        reasons.append("General ecosystem signal; monitor for roadmap impact")

    confidence = min(0.95, confidence + (0.1 if len(reasons) >= 2 else 0.03))

    return Recommendation(
        article_id=int(article["id"]),
        project_id=int(project.id or 0),
        importance_score=round(importance, 1),
        relevance_score=round(relevance, 1),
        confidence_score=round(confidence, 2),
        action=action,
        reasoning="; ".join(reasons[:2]),
    )


def recommendation_to_dict(rec: Recommendation) -> dict:
    return asdict(rec)


def decode_project(row: dict) -> ProjectProfile:
    return ProjectProfile(
        id=row["id"],
        name=row["name"],
        description=row["description"] or "",
        hardware_target=row["hardware_target"] or "",
        deployment_style=row["deployment_style"] or "",
        offline_requirement=row["offline_requirement"] or "",
        latency_sensitivity=row["latency_sensitivity"] or "",
        power_sensitivity=row["power_sensitivity"] or "",
        memory_constraints=row["memory_constraints"] or "",
        preferred_frameworks=json.loads(row["preferred_frameworks"] or "[]"),
        excluded_technologies=json.loads(row["excluded_technologies"] or "[]"),
        categories_of_interest=json.loads(row["categories_of_interest"] or "[]"),
        goals=row["goals"] or "",
        evaluation_priorities=row["evaluation_priorities"] or "",
    )
