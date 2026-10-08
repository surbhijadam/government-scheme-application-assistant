"""Tests for POST /api/eligibility/check."""


def test_eligibility_requires_auth(client, seeded_scheme):
    response = client.post("/api/eligibility/check", json={"scheme_id": seeded_scheme})
    assert response.status_code == 401


def test_eligibility_blocked_without_profile(client, auth_headers, seeded_scheme):
    response = client.post("/api/eligibility/check", headers=auth_headers, json={"scheme_id": seeded_scheme})
    assert response.status_code == 400


def test_eligible_user_passes(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    response = client.post("/api/eligibility/check", headers=auth_headers, json={"scheme_id": seeded_scheme})
    assert response.status_code == 200
    assert response.get_json()["eligible"] is True


def test_ineligible_user_fails_with_reason(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 10})
    response = client.post("/api/eligibility/check", headers=auth_headers, json={"scheme_id": seeded_scheme})
    assert response.status_code == 200
    body = response.get_json()
    assert body["eligible"] is False
    assert len(body["failed_rules"]) == 1
    assert "age" in body["failed_rules"][0]["reason"]


def test_eligibility_check_nonexistent_scheme(client, auth_headers):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    response = client.post("/api/eligibility/check", headers=auth_headers, json={"scheme_id": 999999})
    assert response.status_code == 404


def test_eligibility_check_missing_scheme_id(client, auth_headers):
    response = client.post("/api/eligibility/check", headers=auth_headers, json={})
    assert response.status_code == 400