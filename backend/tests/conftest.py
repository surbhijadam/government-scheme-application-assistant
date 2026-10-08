"""
Shared pytest fixtures for the whole test suite.

Every test gets a FRESH in-memory SQLite database (never real MySQL),
created before the test runs and thrown away after. Tests never depend
on each other's leftover data, and never touch production data.
"""
import os

import pytest

os.environ["TEST_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-minimum-32-bytes"
os.environ["FLASK_DEBUG"] = "False"

from app import create_app  # noqa: E402  (must come after the env vars above)
from app.extensions import db  # noqa: E402
from app.models import EligibilityRule, RequiredDocument, Scheme, User  # noqa: E402


@pytest.fixture
def app():
    """A fresh Flask app with a fresh in-memory database for one test."""
    flask_app = create_app()
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for making requests without running a real server."""
    return app.test_client()


@pytest.fixture
def seeded_scheme(app):
    """A demo scheme with one eligibility rule and one required document."""
    with app.app_context():
        scheme = Scheme()
        scheme.name = "[DEMO] Test Scheme"
        scheme.category = "Education"
        scheme.status = "active"
        db.session.add(scheme)
        db.session.commit()

        db.session.add(
            EligibilityRule(scheme_id=scheme.scheme_id, field_name="age", operator=">=", expected_value="18") #type: ignore
        )
        db.session.add(
            RequiredDocument(scheme_id=scheme.scheme_id, document_name="Test Document", mandatory=True) #type: ignore
        )
        db.session.commit()

        return scheme.scheme_id


def _register_and_login(client, email, password="password123", name="Test User"):
    client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client):
    """A logged-in regular user's auth headers."""
    return _register_and_login(client, "user@example.com")


@pytest.fixture
def other_auth_headers(client):
    """A SECOND, different logged-in user - for testing data isolation."""
    return _register_and_login(client, "otheruser@example.com")


@pytest.fixture
def admin_headers(app, client):
    """A logged-in admin user's auth headers."""
    _register_and_login(client, "admin@example.com")
    with app.app_context():
        user = User.query.filter_by(email="admin@example.com").first()
        assert user is not None, "Admin user was not created during fixture setup"
        user.role = "admin"
        db.session.commit()
    # Log in again - the first token's role claim is stale (still "user")
    return _register_and_login(client, "admin@example.com")