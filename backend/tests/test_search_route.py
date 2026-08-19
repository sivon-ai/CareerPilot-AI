from __future__ import annotations

import sys
import types

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_route_returns_results() -> None:
    response = client.post("/documents/search", json={"query": "career planning and job matching"})
    assert response.status_code == 200
    payload = response.json()
    assert "query" in payload
    assert "results" in payload
    assert isinstance(payload["results"], list)


def test_answer_question_uses_retrieval_context(monkeypatch) -> None:
    from app.services import agent

    captured: dict[str, object] = {}

    def fake_query_documents(query: str, k: int = 5):
        captured["query"] = query
        return {
            "query": query,
            "results": [
                {"page_content": "Use measurable achievements and tailor your resume to each role.", "metadata": {"page": 1}},
            ],
        }

    class FakeResponse:
        text = "Use measurable achievements and tailor each resume bullet to the role."

    class FakeClient:
        class models:
            @staticmethod
            def generate_content(model: str, contents):
                captured["model"] = model
                captured["contents"] = contents
                return FakeResponse()

    google_pkg = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_mod.Client = lambda api_key: FakeClient()
    google_pkg.genai = genai_mod
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = genai_mod

    monkeypatch.setattr(agent, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(agent, "GEMINI_MODEL", "models/gemini-3.6-flash")
    monkeypatch.setattr(agent, "query_documents", fake_query_documents)

    reply = agent.answer_question("How should I tailor my resume?")

    assert reply == "Use measurable achievements and tailor each resume bullet to the role."
    assert captured["query"] == "How should I tailor my resume?"
    assert "Use measurable achievements and tailor your resume to each role." in str(captured["contents"]) 


def test_api_chat_route_returns_reply(monkeypatch) -> None:
    from app.services import rag_service

    monkeypatch.setattr(
        rag_service,
        "answer_question",
        lambda question: {"answer": f"Reply for: {question}", "sources": [{"source": "resume.pdf", "page": 1}]},
    )

    response = client.post("/api/chat", json={"message": "Hello there"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "Reply for: Hello there"
    assert payload["sources"][0]["source"] == "resume.pdf"


def test_chat_route_requires_non_empty_message() -> None:
    response = client.post("/api/chat", json={"message": " "})

    assert response.status_code == 422


def test_rag_chat_service_returns_answer_and_sources(monkeypatch) -> None:
    from app.services import rag_service

    class FakeResult:
        def __init__(self):
            self.page_content = "Python, Java, SQL, and FastAPI experience."
            self.metadata = {"document_id": "doc-123", "source": "resume.pdf", "page": 1, "score": 0.92}

    monkeypatch.setattr(rag_service, "generate_query_embedding", lambda query: [0.1, 0.2, 0.3])
    monkeypatch.setattr(rag_service, "search_similar_chunks", lambda embedding, k=5: [FakeResult()])
    monkeypatch.setattr(rag_service, "generate_answer", lambda question, context: "The candidate has experience with Python, Java, SQL, and FastAPI.")

    result = rag_service.answer_question("What programming languages does the candidate know?")

    assert result["answer"] == "The candidate has experience with Python, Java, SQL, and FastAPI."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source"] == "resume.pdf"


def test_api_health_allows_frontend_origin() -> None:
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_validate_gemini_connection_handles_quota_exhaustion(monkeypatch) -> None:
    from app.services import gemini_service

    class FakeQuotaError(Exception):
        pass

    class FakeClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                raise FakeQuotaError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(gemini_service, "get_gemini_client", lambda: FakeClient())

    assert gemini_service.validate_gemini_connection() is False


def test_answer_question_returns_user_friendly_quota_message(monkeypatch) -> None:
    from app.services import agent

    monkeypatch.setattr(agent, "GEMINI_API_KEY", "test-key")

    class FakeQuotaError(Exception):
        pass

    def fake_generate_content(*args, **kwargs):
        raise FakeQuotaError("429 RESOURCE_EXHAUSTED")

    class FakeClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                return fake_generate_content(*args, **kwargs)

    monkeypatch.setattr(agent, "_format_retrieval_context", lambda question: "some context")

    import google
    import types

    google_pkg = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_mod.Client = lambda api_key: FakeClient()
    google_pkg.genai = genai_mod
    monkeypatch.setitem(__import__("sys").modules, "google", google_pkg)
    monkeypatch.setitem(__import__("sys").modules, "google.genai", genai_mod)

    reply = agent.answer_question("How should I tailor my resume?")

    assert "quota" in reply.lower()
    assert "429" not in reply


def test_career_match_route_returns_ranked_matches() -> None:
    response = client.post(
        "/api/career/match",
        json={
            "resume_text": "Python, SQL, analytics, dashboards, project management, communication",
            "jobs": [
                {"title": "Senior Data Analyst", "requirements": "Python SQL analytics dashboards"},
                {"title": "Frontend Engineer", "requirements": "React TypeScript CSS UX"},
                {"title": "Product Manager", "requirements": "strategy roadmaps stakeholder communication"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["matches"][0]["title"] == "Senior Data Analyst"
    assert payload["matches"][0]["score"] >= 0
