"""Tests for GET /api/schemes and GET /api/schemes/<id> (public, no auth needed)."""


def test_list_schemes_no_auth_required(client, seeded_scheme):
    response = client.get("/api/schemes")
    assert response.status_code == 200
    assert response.get_json()["count"] >= 1


def test_search_schemes_by_name(client, seeded_scheme):
    response = client.get("/api/schemes?search=Test Scheme")
    assert response.status_code == 200
    assert response.get_json()["count"] == 1


def test_search_schemes_no_match(client, seeded_scheme):
    response = client.get("/api/schemes?search=ZZZNoMatch")
    assert response.get_json()["count"] == 0


def test_filter_schemes_by_category(client, seeded_scheme):
    response = client.get("/api/schemes?category=Education")
    assert response.get_json()["count"] == 1


def test_get_scheme_detail_includes_rules_and_documents(client, seeded_scheme):
    response = client.get(f"/api/schemes/{seeded_scheme}")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["eligibility_rules"]) == 1
    assert len(body["required_documents"]) == 1


def test_get_nonexistent_scheme_returns_404(client):
    response = client.get("/api/schemes/999999")
    assert response.status_code == 404