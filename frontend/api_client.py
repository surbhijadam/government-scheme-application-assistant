"""
Every call from Streamlit to the Flask backend goes through this module.

Keeping this separate means:
- The Flask base URL and token-handling logic live in exactly one place.
- Streamlit pages never build raw HTTP requests themselves, which keeps
  pages focused purely on display/input, not business logic.
"""
import os

import requests
import streamlit as st
from dotenv import load_dotenv

# Load the .env file sitting next to THIS file specifically. Calling
# load_dotenv() with no path searches upward through parent directories
# for any .env it can find, which can silently pick up an unrelated file
# if Streamlit is ever launched from a different working directory.
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000/api")


def _auth_headers():
    """Build the Authorization header from the token stored in session_state."""
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _handle_response(response):
    """Return (data, error_message). Exactly one of them is not None."""
    try:
        data = response.json()
    except ValueError:
        return None, f"Server returned an unexpected response (status {response.status_code})"

    if response.status_code >= 400:
        return None, data.get("error", f"Request failed (status {response.status_code})")

    return data, None


def register(name, email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"name": name, "email": email, "password": password},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def login(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def get_profile():
    try:
        response = requests.get(f"{API_BASE_URL}/profile", headers=_auth_headers(), timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def update_profile(profile_data):
    try:
        response = requests.put(
            f"{API_BASE_URL}/profile", headers=_auth_headers(), json=profile_data, timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def list_schemes(search="", category=""):
    params = {}
    if search:
        params["search"] = search
    if category:
        params["category"] = category
    try:
        response = requests.get(f"{API_BASE_URL}/schemes", params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def get_scheme(scheme_id):
    try:
        response = requests.get(f"{API_BASE_URL}/schemes/{scheme_id}", timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def check_eligibility(scheme_id):
    try:
        response = requests.post(
            f"{API_BASE_URL}/eligibility/check",
            headers=_auth_headers(),
            json={"scheme_id": scheme_id},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def get_recommendations():
    try:
        response = requests.get(f"{API_BASE_URL}/recommendations", headers=_auth_headers(), timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def create_application(scheme_id):
    """
    Returns (data, error). On a 409 (duplicate active application), the
    backend includes the EXISTING application_id in its body - the generic
    handler would discard that and keep only the message, so this returns
    the full body as data even on error, letting the page offer a direct
    link to the existing draft instead of just an error string.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/applications",
            headers=_auth_headers(),
            json={"scheme_id": scheme_id},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"

    try:
        body = response.json()
    except ValueError:
        return None, f"Server returned an unexpected response (status {response.status_code})"

    if response.status_code >= 400:
        return body, body.get("error", "Request failed")
    return body, None


def list_applications():
    try:
        response = requests.get(f"{API_BASE_URL}/applications", headers=_auth_headers(), timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def get_application(application_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/applications/{application_id}", headers=_auth_headers(), timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def get_application_status(application_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/applications/{application_id}/status", headers=_auth_headers(), timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def withdraw_application(application_id):
    try:
        response = requests.put(
            f"{API_BASE_URL}/applications/{application_id}",
            headers=_auth_headers(),
            json={"status": "withdrawn"},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def submit_application(application_id):
    """
    Returns (data, error). On a 400 'incomplete application' response, the
    backend includes a 'blockers' list (Phase 8) - the generic error handler
    would discard that and keep only the top-level message, so this function
    folds each blocker onto its own line instead of losing that detail.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/applications/{application_id}/submit", headers=_auth_headers(), timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"

    try:
        body = response.json()
    except ValueError:
        return None, f"Server returned an unexpected response (status {response.status_code})"

    if response.status_code >= 400:
        if "blockers" in body:
            blocker_lines = "\n".join(f"- {reason}" for reason in body["blockers"])
            return None, f"{body.get('error', 'Cannot submit')}:\n{blocker_lines}"
        return None, body.get("error", "Request failed")

    return body, None


def get_document_checklist(application_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/applications/{application_id}/documents", headers=_auth_headers(), timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def upload_document(application_id, document_id, uploaded_file):
    """uploaded_file: a Streamlit UploadedFile (has .name, .type, .getvalue())."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/applications/{application_id}/documents",
            headers=_auth_headers(),
            data={"document_id": str(document_id)},
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


# ---- Admin-only functions (require role == "admin" on the logged-in user) ----

def admin_list_applications(status_filter=""):
    params = {"status": status_filter} if status_filter else {}
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/applications", headers=_auth_headers(), params=params, timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_update_application_status(application_id, new_status, remarks=""):
    """
    Returns (data, error). On a 400 invalid-transition response, the backend
    includes 'allowed_next_statuses' - surfaced here the same way
    submit_application surfaces 'blockers', instead of being discarded.
    """
    try:
        response = requests.put(
            f"{API_BASE_URL}/admin/applications/{application_id}/status",
            headers=_auth_headers(),
            json={"status": new_status, "remarks": remarks},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"

    try:
        body = response.json()
    except ValueError:
        return None, f"Server returned an unexpected response (status {response.status_code})"

    if response.status_code >= 400:
        if "allowed_next_statuses" in body:
            allowed = ", ".join(body["allowed_next_statuses"]) or "(none from here - it may need to be submitted first, or it's already final)"
            return None, f"{body.get('error', 'Invalid transition')}. Allowed next: {allowed}"
        return None, body.get("error", "Request failed")

    return body, None


def admin_create_scheme(scheme_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/schemes", headers=_auth_headers(), json=scheme_data, timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_update_scheme(scheme_id, updates):
    try:
        response = requests.put(
            f"{API_BASE_URL}/admin/schemes/{scheme_id}", headers=_auth_headers(), json=updates, timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_add_rule(scheme_id, field_name, operator_symbol, expected_value):
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/schemes/{scheme_id}/rules",
            headers=_auth_headers(),
            json={"field_name": field_name, "operator": operator_symbol, "expected_value": expected_value},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_delete_rule(scheme_id, rule_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/admin/schemes/{scheme_id}/rules/{rule_id}", headers=_auth_headers(), timeout=10
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_add_document(scheme_id, document_name, mandatory):
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/schemes/{scheme_id}/documents",
            headers=_auth_headers(),
            json={"document_name": document_name, "mandatory": mandatory},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def admin_delete_document(scheme_id, document_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/admin/schemes/{scheme_id}/documents/{document_id}",
            headers=_auth_headers(),
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)


def ask_assistant(message, scheme_id=None):
    payload = {"message": message}
    if scheme_id:
        payload["scheme_id"] = scheme_id
    try:
        response = requests.post(
            f"{API_BASE_URL}/assistant/chat", headers=_auth_headers(), json=payload, timeout=30
        )
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the server. Is the Flask backend running?"
    return _handle_response(response)