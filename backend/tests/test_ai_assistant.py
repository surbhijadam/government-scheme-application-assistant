"""
Tests for POST /api/assistant/chat, focused on graceful AI failure.

No test here mocks Groq into SUCCEEDING, because that would require a real
API key and real network access. Instead, these confirm the thing the SRS
actually requires: if the AI is unavailable, the endpoint degrades cleanly
AND the rest of the application keeps working normally.
"""


def test_chat_requires_auth(client):
    response = client.post("/api/assistant/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_chat_requires_a_message(client, auth_headers):
    response = client.post("/api/assistant/chat", headers=auth_headers, json={"message": ""})
    assert response.status_code == 400


def test_chat_with_nonexistent_scheme_id(client, auth_headers):
    response = client.post(
        "/api/assistant/chat", headers=auth_headers, json={"message": "hi", "scheme_id": 999999}
    )
    assert response.status_code == 404


def test_ai_unavailable_degrades_gracefully(client, auth_headers, monkeypatch):
    """With no GROQ_API_KEY set, the endpoint must return 503, not crash."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = client.post("/api/assistant/chat", headers=auth_headers, json={"message": "What is this scheme?"})
    assert response.status_code == 503
    assert "unavailable" in response.get_json()["error"].lower()


def test_core_app_unaffected_by_ai_failure(client, auth_headers, seeded_scheme, monkeypatch):
    """The whole point of isolating the AI call: everything else must keep
    working even while the assistant is completely unavailable."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    # AI fails...
    ai_response = client.post("/api/assistant/chat", headers=auth_headers, json={"message": "hi"})
    assert ai_response.status_code == 503

    # ...but the core deterministic features are completely unaffected
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    eligibility_response = client.post(
        "/api/eligibility/check", headers=auth_headers, json={"scheme_id": seeded_scheme}
    )
    assert eligibility_response.status_code == 200
    assert eligibility_response.get_json()["eligible"] is True

    health_response = client.get("/api/health")
    assert health_response.status_code == 200