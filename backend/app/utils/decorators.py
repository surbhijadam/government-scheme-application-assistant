from functools import wraps

import jwt
from flask import g, jsonify, request

from app.utils.jwt_utils import decode_token


def _verify_token_and_set_g():
    """Shared logic: read the Authorization header, verify the JWT, populate g.
    Returns an error (response, status) tuple, or None if verification succeeded."""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or malformed Authorization header"}), 401

    token = auth_header.split(" ", 1)[1]

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    g.current_user_id = payload["user_id"]
    g.current_user_role = payload["role"]
    return None


def login_required(view_function):
    """Require a valid JWT in the Authorization header before running the view."""

    @wraps(view_function)
    def wrapper(*args, **kwargs):
        error = _verify_token_and_set_g()
        if error:
            return error
        return view_function(*args, **kwargs)

    return wrapper


def admin_required(view_function):
    """Require a valid JWT AND an admin role before running the view."""

    @wraps(view_function)
    def wrapper(*args, **kwargs):
        error = _verify_token_and_set_g()
        if error:
            return error

        if g.current_user_role != "admin":
            return jsonify({"error": "Admin access required"}), 403

        return view_function(*args, **kwargs)

    return wrapper