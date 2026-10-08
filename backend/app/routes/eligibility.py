from flask import Blueprint, g, jsonify, request

from app.models import Scheme, UserProfile
from app.services.eligibility_engine import check_eligibility
from app.utils.decorators import login_required
from app.extensions import db

eligibility_bp = Blueprint("eligibility", __name__)


@eligibility_bp.route("/eligibility/check", methods=["POST"])
@login_required
def check_eligibility_route():
    """Check the logged-in user's eligibility for a given scheme."""
    data = request.get_json(silent=True) or {}
    scheme_id = data.get("scheme_id")

    if not scheme_id:
        return jsonify({"error": "scheme_id is required"}), 400

    scheme = db.session.get(Scheme, scheme_id)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    profile = UserProfile.query.filter_by(user_id=g.current_user_id).first()
    if not profile:
        return jsonify({"error": "Complete your profile first at PUT /api/profile"}), 400

    profile_data = {
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "income": float(profile.income) if profile.income is not None else None,
        "occupation": profile.occupation,
        "category": profile.category,
    }

    scheme_rules = list(getattr(scheme, "eligibility_rules", []) or [])
    rules = [
        {
            "field_name": rule.field_name,
            "operator": rule.operator,
            "expected_value": rule.expected_value,
        }
        for rule in scheme_rules
    ]

    result = check_eligibility(profile_data, rules)

    return (
        jsonify(
            {
                "scheme_id": scheme.scheme_id,
                "scheme_name": scheme.name,
                **result,
            }
        ),
        200,
    )