"""Tests for admin-only endpoints and role-based access control."""


def test_admin_endpoint_requires_auth_at_all(client):
    response = client.post("/api/admin/schemes", json={"name": "Hacked"})
    assert response.status_code == 401


def test_regular_user_blocked_from_admin_endpoints(client, auth_headers):
    response = client.post("/api/admin/schemes", headers=auth_headers, json={"name": "Hacked"})
    assert response.status_code == 403


def test_regular_user_blocked_from_admin_applications_list(client, auth_headers):
    response = client.get("/api/admin/applications", headers=auth_headers)
    assert response.status_code == 403


def test_admin_can_create_scheme(client, admin_headers):
    response = client.post("/api/admin/schemes", headers=admin_headers, json={"name": "[DEMO] Admin Scheme"})
    assert response.status_code == 201


def test_admin_can_list_all_applications_across_users(client, admin_headers, auth_headers, seeded_scheme):
    client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})

    response = client.get("/api/admin/applications", headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()["count"] == 1


def test_admin_cannot_move_draft_application(client, admin_headers, auth_headers, seeded_scheme):
    """An admin should never be able to push a DRAFT application forward -
    only the applicant decides when to submit it."""
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    response = client.put(
        f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "under_review"}
    )
    assert response.status_code == 400


def test_admin_can_approve_from_under_review(client, admin_headers, auth_headers, seeded_scheme):
    import io

    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    scheme_detail = client.get(f"/api/schemes/{seeded_scheme}").get_json()
    document_id = scheme_detail["required_documents"][0]["document_id"]
    client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        data={"document_id": str(document_id), "file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf")},
        content_type="multipart/form-data",
    )
    client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)

    client.put(f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "under_review"})
    response = client.put(
        f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "approved"}
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "approved"


def test_cannot_change_status_after_final(client, admin_headers, auth_headers, seeded_scheme):
    import io

    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    created = client.post("/api/applications", headers=auth_headers, json={"scheme_id": seeded_scheme})
    app_id = created.get_json()["application_id"]

    scheme_detail = client.get(f"/api/schemes/{seeded_scheme}").get_json()
    document_id = scheme_detail["required_documents"][0]["document_id"]
    client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        data={"document_id": str(document_id), "file": (io.BytesIO(b"%PDF-1.4"), "doc.pdf")},
        content_type="multipart/form-data",
    )
    client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    client.put(f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "under_review"})
    client.put(f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "approved"})

    response = client.put(
        f"/api/admin/applications/{app_id}/status", headers=admin_headers, json={"status": "rejected"}
    )
    assert response.status_code == 409