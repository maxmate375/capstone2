from fastapi.testclient import TestClient

from api import main as api_main
from api.main import app, get_feedback_store
from src.tools.feedback_store import FeedbackStore


class FakeAssistant:
    def __init__(self):
        self.received_profile = None

    def query(self, query, session_id, profile=None):
        self.received_profile = profile
        return {
            "answer": "A source-grounded answer.",
            "sources": [{
                "title": "Central scheme",
                "citation": "MyScheme public dataset",
                "url": "https://www.myscheme.gov.in/schemes/example",
                "official_url": "https://example.gov.in",
                "ministry": "Ministry",
            }],
            "retrieved_context": ["Evidence text."],
            "eligibility_matches": [],
            "agents_invoked": ["planner", "retriever", "validator"],
            "confidence": 0.9,
        }


def test_query_and_feedback_endpoints(tmp_path, monkeypatch):
    assistant = FakeAssistant()
    monkeypatch.setattr(api_main, "get_assistant", lambda: assistant)
    app.dependency_overrides[get_feedback_store] = lambda: FeedbackStore(
        tmp_path / "feedback.sqlite3"
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/query",
                json={
                    "query": "What does the scheme say?",
                    "profile": {"age": 35, "state": "Maharashtra", "is_farmer": True},
                },
            )
            assert response.status_code == 200
            result = response.json()
            assert result["answer"] == "A source-grounded answer."
            assert result["agents_invoked"] == ["planner", "retriever", "validator"]
            assert result["session_id"]
            assert assistant.received_profile == {
                "age": 35,
                "state": "Maharashtra",
                "is_farmer": True,
            }

            feedback = client.post(
                "/feedback",
                json={
                    "session_id": result["session_id"],
                    "query": "What does the scheme say?",
                    "rating": 1,
                    "correction": "Please include eligibility details.",
                },
            )
            assert feedback.status_code == 200
            assert feedback.json()["status"] == "recorded"
    finally:
        app.dependency_overrides.clear()


def test_query_rejects_empty_or_too_short_query():
    with TestClient(app) as client:
        response = client.post("/query", json={"query": "  "})
    assert response.status_code == 422


def test_health_endpoint_does_not_require_model_configuration():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
