from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.models import UserProfile
from app.utils.decorators import login_required

profile_bp = Blueprint("profile", __name__)

ALLOWED_CATEGORIES = {"General", "OBC", "SC", "ST", "EWS"}
ALLOWED_GENDERS = {"Male", "Female", "Other"}


@profile_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Return the logged-in user's profile."""
    profile = UserProfile.query.filter_by(user_id=g.current_user_id).first()

    if not profile:
        return jsonify({"error": "Profile not found. Create one with PUT /api/profile"}), 404

    return jsonify(_serialize_profile(profile)), 200


@profile_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    """Create or update the logged-in user's profile."""
    data = request.get_json(silent=True) or {}

    error = _validate_profile_data(data)
    if error:
        return jsonify({"error": error}), 400

    profile = UserProfile.query.filter_by(user_id=g.current_user_id).first()
    if not profile:
        profile = UserProfile()
        profile.user_id = g.current_user_id
        db.session.add(profile)

    for field in ("age", "gender", "state", "income", "occupation", "category", "other_details"):
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()

    return jsonify(_serialize_profile(profile)), 200


def _validate_profile_data(data):
    """Return an error message string if invalid, or None if valid."""
    if "age" in data:
        age = data["age"]
        if not isinstance(age, int) or age < 0 or age > 120:
            return "Age must be a whole number between 0 and 120"

    if "income" in data:
        income = data["income"]
        if not isinstance(income, (int, float)) or income < 0:
            return "Income must be a non-negative number"

    if "gender" in data and data["gender"] not in ALLOWED_GENDERS:
        return f"Gender must be one of: {', '.join(sorted(ALLOWED_GENDERS))}"

    if "category" in data and data["category"] not in ALLOWED_CATEGORIES:
        return f"Category must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}"

    return None


def _serialize_profile(profile):
    """Convert a UserProfile model into a plain dictionary for JSON output."""
    return {
        "profile_id": profile.profile_id,
        "user_id": profile.user_id,
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "income": float(profile.income) if profile.income is not None else None,
        "occupation": profile.occupation,
        "category": profile.category,
        "other_details": profile.other_details,
    }