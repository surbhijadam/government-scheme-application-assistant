"""Tests for GET /api/recommendations."""


def test_recommendations_requires_auth(client):
    response = client.get("/api/recommendations")
    assert response.status_code == 401


def test_recommendations_blocked_without_profile(client, auth_headers):
    response = client.get("/api/recommendations", headers=auth_headers)
    assert response.status_code == 400


def test_matching_scheme_is_recommended(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    response = client.get("/api/recommendations", headers=auth_headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 1
    assert body["recommendations"][0]["scheme_id"] == seeded_scheme


def test_non_matching_profile_gets_no_recommendations(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 5})
    response = client.get("/api/recommendations", headers=auth_headers)
    assert response.get_json()["count"] == 0