from __future__ import annotations

import re
from pathlib import Path

from .models import ArticleRecord


ARTICLE_RE = re.compile(
    r"- \*\*(?P<title>.+?)\*\*(?:\s+—\s+_(?P<published>.+?)_)?\n"
    r"(?:\s+>\s(?P<summary>.+?)\n)?\s+\[Read more\]\((?P<url>https?://[^)]+)\)",
    re.MULTILINE,
)


def infer_metadata(text: str) -> tuple[str, str, list[str]]:
    low = text.lower()
    edge_terms = ["edge", "on-device", "embedded", "jetson", "orin", "real-time", "quantization", "tensorrt", "onnx", "cuda"]
    doc_terms = ["document", "ocr", "retrieval", "rag", "pdf", "knowledge base"]
    multi_terms = ["multimodal", "audio", "vision", "video", "image"]

    tags: list[str] = []
    deployment_fit = "general"
    modality = "text"

    if any(t in low for t in edge_terms):
        deployment_fit = "edge"
        tags.append("edge")
    if any(t in low for t in doc_terms):
        tags.append("document-ai")
    if any(t in low for t in multi_terms):
        modality = "multimodal"
        tags.append("multimodal")

    entities = sorted(set(re.findall(r"\b(OpenAI|NVIDIA|Google|DeepMind|Anthropic|Meta|Microsoft|Jetson|Gemma|Llama|Mistral|Claude|Gemini)\b", text, re.I)))
    return modality, deployment_fit, entities


def parse_report(markdown_path: Path) -> list[ArticleRecord]:
    content = markdown_path.read_text(encoding="utf-8")
    report_date_match = re.search(r"AI News Report\s+—\s+(\d{4}-\d{2}-\d{2})", content)
    report_date = report_date_match.group(1) if report_date_match else ""

    results: list[ArticleRecord] = []
    current_category = ""
    current_source = ""

    for line in content.splitlines():
        if line.startswith("## ") and not line.startswith("## 📊"):
            current_category = re.sub(r"^##\s+[\W_]*", "", line).strip()
        elif line.startswith("### "):
            current_source = line.replace("###", "").strip()

    for m in ARTICLE_RE.finditer(content):
        title = m.group("title").strip()
        summary = (m.group("summary") or "").strip()
        url = m.group("url").strip()
        published = (m.group("published") or "").strip()
        metadata_text = " ".join([title, summary, url])
        modality, deployment_fit, entities = infer_metadata(metadata_text)
        dedupe_key = re.sub(r"\W+", "", title.lower())[:80]

        block_before = content[:m.start()]
        category_match = re.findall(r"##\s+[\W_]*([^\n]+)", block_before)
        source_match = re.findall(r"###\s+([^\n]+)", block_before)
        category = category_match[-1].strip() if category_match else current_category
        source = source_match[-1].strip() if source_match else current_source

        results.append(
            ArticleRecord(
                report_date=report_date,
                category=category,
                source=source,
                title=title,
                published_date=published,
                summary=summary,
                tags=list(set([t.lower() for t in entities] + ([] if not deployment_fit else [deployment_fit]))),
                url=url,
                modality=modality,
                deployment_fit=deployment_fit,
                entities=entities,
                dedupe_key=dedupe_key,
            )
        )

    return results
