from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.utils.jwt_utils import generate_token
from app.utils.validators import is_valid_email, is_valid_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Create a new user account."""
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "Name is required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "A valid email is required"}), 400

    if not is_valid_password(password):
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "An account with this email already exists"}), 409

    new_user = User(
        name=name,  #type: ignore
        email=email,  #type: ignore
        password_hash=generate_password_hash(password),  #type: ignore
        role="user",  #type: ignore
    )
    db.session.add(new_user)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Registration successful",
                "user": {
                    "user_id": new_user.user_id,
                    "name": new_user.name,
                    "email": new_user.email,
                    "role": new_user.role,
                },
            }
        ),
        201,
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user.user_id, user.role)

    return (
        jsonify(
            {
                "message": "Login successful",
                "token": token,
                "user": {
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                },
            }
        ),
        200,
    )