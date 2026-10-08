"""Tests for POST /api/applications/<id>/submit - completeness validation."""
import io


def _create_draft(client, auth_headers, scheme_id):
    response = client.post("/api/applications", headers=auth_headers, json={"scheme_id": scheme_id})
    return response.get_json()["application_id"]


def test_submit_blocked_with_no_profile(client, auth_headers, seeded_scheme):
    app_id = _create_draft(client, auth_headers, seeded_scheme)
    response = client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    assert response.status_code == 400
    assert "blockers" in response.get_json()


def test_submit_blocked_when_ineligible(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 5})  # fails age >= 18
    app_id = _create_draft(client, auth_headers, seeded_scheme)

    response = client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    assert response.status_code == 400
    assert any("age" in reason for reason in response.get_json()["blockers"])


def test_submit_blocked_when_missing_mandatory_document(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})  # eligible, but no document uploaded
    app_id = _create_draft(client, auth_headers, seeded_scheme)

    response = client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    assert response.status_code == 400
    assert any("document" in reason.lower() for reason in response.get_json()["blockers"])


def test_submit_succeeds_once_complete(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    app_id = _create_draft(client, auth_headers, seeded_scheme)

    # Upload the one mandatory document the seeded scheme requires
    scheme_detail = client.get(f"/api/schemes/{seeded_scheme}").get_json()
    document_id = scheme_detail["required_documents"][0]["document_id"]

    client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        data={"document_id": str(document_id), "file": (io.BytesIO(b"%PDF-1.4 fake"), "doc.pdf")},
        content_type="multipart/form-data",
    )

    response = client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["status"] == "submitted"


def test_cannot_resubmit_already_submitted_application(client, auth_headers, seeded_scheme):
    client.put("/api/profile", headers=auth_headers, json={"age": 25})
    app_id = _create_draft(client, auth_headers, seeded_scheme)

    scheme_detail = client.get(f"/api/schemes/{seeded_scheme}").get_json()
    document_id = scheme_detail["required_documents"][0]["document_id"]
    client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        data={"document_id": str(document_id), "file": (io.BytesIO(b"%PDF-1.4 fake"), "doc.pdf")},
        content_type="multipart/form-data",
    )
    client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)

    second_attempt = client.post(f"/api/applications/{app_id}/submit", headers=auth_headers)
    assert second_attempt.status_code == 409


def test_document_wrong_file_type_rejected(client, auth_headers, seeded_scheme):
    app_id = _create_draft(client, auth_headers, seeded_scheme)
    scheme_detail = client.get(f"/api/schemes/{seeded_scheme}").get_json()
    document_id = scheme_detail["required_documents"][0]["document_id"]

    response = client.post(
        f"/api/applications/{app_id}/documents",
        headers=auth_headers,
        data={"document_id": str(document_id), "file": (io.BytesIO(b"bad"), "virus.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400