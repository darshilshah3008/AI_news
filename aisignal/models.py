from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ArticleRecord:
    id: int | None = None
    report_date: str = ""
    category: str = ""
    source: str = ""
    title: str = ""
    published_date: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    url: str = ""
    modality: str = "unknown"
    deployment_fit: str = "general"
    entities: list[str] = field(default_factory=list)
    dedupe_key: str = ""
    created_at: datetime | None = None


@dataclass
class ProjectProfile:
    id: int | None = None
    name: str = ""
    description: str = ""
    hardware_target: str = ""
    deployment_style: str = ""
    offline_requirement: str = ""
    latency_sensitivity: str = ""
    power_sensitivity: str = ""
    memory_constraints: str = ""
    preferred_frameworks: list[str] = field(default_factory=list)
    excluded_technologies: list[str] = field(default_factory=list)
    categories_of_interest: list[str] = field(default_factory=list)
    goals: str = ""
    evaluation_priorities: str = ""


@dataclass
class Recommendation:
    article_id: int
    project_id: int
    importance_score: float
    relevance_score: float
    confidence_score: float
    action: str
    reasoning: str
