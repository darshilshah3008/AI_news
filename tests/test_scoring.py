from aisignal.models import ProjectProfile
from aisignal.scoring import score_article


def test_scoring_edge_project_prefers_edge_terms():
    project = ProjectProfile(
        id=1,
        name="Orin Nano Edge Assistant",
        description="edge project",
        hardware_target="NVIDIA Orin Nano",
        deployment_style="edge/local",
        preferred_frameworks=["TensorRT", "ONNX"],
    )
    article = {
        "id": 1,
        "title": "New quantization path for Jetson with TensorRT",
        "summary": "real-time edge inference on device",
        "category": "Research",
        "deployment_fit": "edge",
        "modality": "text",
    }
    rec = score_article(article, project)
    assert rec.relevance_score >= 60
    assert rec.action in {"BUILD", "TEST", "LEARN"}
