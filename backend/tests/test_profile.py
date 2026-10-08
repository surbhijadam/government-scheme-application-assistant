"""Tests for GET/PUT /api/profile."""


def test_get_profile_requires_auth(client):
    response = client.get("/api/profile")
    assert response.status_code == 401


def test_get_profile_before_creation_returns_404(client, auth_headers):
    response = client.get("/api/profile", headers=auth_headers)
    assert response.status_code == 404


def test_create_and_get_profile(client, auth_headers):
    put_response = client.put(
        "/api/profile",
        headers=auth_headers,
        json={"age": 25, "state": "Madhya Pradesh", "occupation": "Student"},
    )
    assert put_response.status_code == 200

    get_response = client.get("/api/profile", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.get_json()["age"] == 25
    assert get_response.get_json()["state"] == "Madhya Pradesh"


def test_partial_update_preserves_other_fields(client, auth_headers):
    client.put("/api/profile", headers=auth_headers, json={"age": 25, "occupation": "Student"})
    client.put("/api/profile", headers=auth_headers, json={"income": 300000})

    response = client.get("/api/profile", headers=auth_headers)
    body = response.get_json()
    assert body["age"] == 25
    assert body["occupation"] == "Student"
    assert body["income"] == 300000.0


def test_invalid_age_rejected(client, auth_headers):
    response = client.put("/api/profile", headers=auth_headers, json={"age": 500})
    assert response.status_code == 400


def test_invalid_category_rejected(client, auth_headers):
    response = client.put("/api/profile", headers=auth_headers, json={"category": "NotARealCategory"})
    assert response.status_code == 400


def test_users_cannot_see_each_others_profile(client, auth_headers, other_auth_headers):
    """Data isolation: user A's profile must never be visible via user B's token."""
    client.put("/api/profile", headers=auth_headers, json={"age": 99, "occupation": "SecretJob"})

    response = client.get("/api/profile", headers=other_auth_headers)
    # Either no profile at all (404) or, if one exists, it must not be user A's data
    if response.status_code == 200:
        assert response.get_json().get("occupation") != "SecretJob"
    else:
        assert response.status_code == 404