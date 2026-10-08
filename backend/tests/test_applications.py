"""Tests for the application lifecycle: create, list, get, withdraw."""


def test_create_application_requires_auth(client, seeded_scheme):
    response = client.post("/api/applications", json={"scheme_id": seeded_scheme})
    assert response.status_code == 401


def test_create_application_success(client, auth_headers, seeded_scheme):
    response = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    assert response.status_code == 201
    assert response.get_json()["status"] == "draft"


def test_duplicate_active_application_rejected(client, auth_headers, seeded_scheme):
    client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    response = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    assert response.status_code == 409
    assert "application_id" in response.get_json()


def test_create_application_nonexistent_scheme(client, auth_headers):
    response = client.post("/api/applications", headers=auth_headers, json={"scheme_id": 999999})
    assert response.status_code == 404


def test_list_applications_only_shows_own(client, auth_headers, other_auth_headers, seeded_scheme):
    client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})

    own_list = client.get("/api/applications", headers=auth_headers)
    other_list = client.get("/api/applications", headers=other_auth_headers)

    assert own_list.get_json()["count"] == 1
    assert other_list.get_json()["count"] == 0


def test_cannot_view_someone_elses_application(client, auth_headers, other_auth_headers, seeded_scheme):
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    response = client.get(f"/api/applications/{app_id}", headers=other_auth_headers)
    assert response.status_code == 404  # not 403 - existence itself is hidden


def test_withdraw_draft_application(client, auth_headers, seeded_scheme):
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    response = client.put(f"/api/applications/{app_id}", headers=auth_headers, json={"status": "withdrawn"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "withdrawn"


def test_cannot_withdraw_twice(client, auth_headers, seeded_scheme):
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    client.put(f"/api/applications/{app_id}", headers=auth_headers, json={"status": "withdrawn"})
    second_attempt = client.put(f"/api/applications/{app_id}", headers=auth_headers, json={"status": "withdrawn"})
    assert second_attempt.status_code == 409


def test_cannot_set_arbitrary_status_via_put(client, auth_headers, seeded_scheme):
    """A user must never be able to self-approve by PUTting an arbitrary status."""
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    response = client.put(f"/api/applications/{app_id}", headers=auth_headers, json={"status": "approved"})
    assert response.status_code == 400