"""Tests for POST /api/auth/register and POST /api/auth/login."""


def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "alice@example.com"
    assert "password" not in body["user"]


def test_register_duplicate_email_fails(client):
    client.post("/api/auth/register", json={"name": "Alice", "email": "dup@example.com", "password": "password123"})
    response = client.post(
        "/api/auth/register", json={"name": "Alice Again", "email": "dup@example.com", "password": "password123"}
    )
    assert response.status_code == 409


def test_register_weak_password_fails(client):
    response = client.post(
        "/api/auth/register", json={"name": "Alice", "email": "weak@example.com", "password": "123"}
    )
    assert response.status_code == 400


def test_register_invalid_email_fails(client):
    response = client.post(
        "/api/auth/register", json={"name": "Alice", "email": "not-an-email", "password": "password123"}
    )
    assert response.status_code == 400


def test_register_missing_name_fails(client):
    response = client.post(
        "/api/auth/register", json={"email": "noname@example.com", "password": "password123"}
    )
    assert response.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register", json={"name": "Bob", "email": "bob@example.com", "password": "password123"})
    response = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_login_wrong_password_fails(client):
    client.post("/api/auth/register", json={"name": "Bob", "email": "bob2@example.com", "password": "password123"})
    response = client.post("/api/auth/login", json={"email": "bob2@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_nonexistent_email_fails(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert response.status_code == 401


def test_login_error_message_does_not_reveal_which_field_was_wrong(client):
    """Wrong password and nonexistent email should return the SAME message,
    so an attacker can't use the error to discover which emails exist."""
    client.post("/api/auth/register", json={"name": "Bob", "email": "bob3@example.com", "password": "password123"})
    wrong_password = client.post("/api/auth/login", json={"email": "bob3@example.com", "password": "wrong"})
    no_such_user = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "wrong"})
    assert wrong_password.get_json()["error"] == no_such_user.get_json()["error"]