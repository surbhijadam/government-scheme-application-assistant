from flask import Blueprint, g, jsonify

from app.models import Scheme, UserProfile
from app.services.eligibility_engine import check_eligibility
from app.utils.decorators import login_required
from app.services.deadline import get_deadline_info

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/recommendations", methods=["GET"])
@login_required
def get_recommendations():
    """Return every active scheme the logged-in user is currently eligible for."""
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

    active_schemes = Scheme.query.filter_by(status="active").order_by(Scheme.name).all()

    recommendations = []
    for scheme in active_schemes:
        rules = [
            {
                "field_name": rule.field_name,
                "operator": rule.operator,
                "expected_value": rule.expected_value,
            }
            for rule in scheme.eligibility_rules
        ]

        result = check_eligibility(profile_data, rules)

        if result["eligible"]:
            deadline_info = get_deadline_info(scheme.deadline)

            recommendations.append(
                {
                    "scheme_id": scheme.scheme_id,
                    "name": scheme.name,
                    "description": scheme.description,
                    "matched_rules": result["matched_rules"],
                    "deadline": 
                        scheme.deadline.isoformat() 
                        if scheme.deadline 
                        else None,                    
                    "days_remaining": deadline_info["days_remaining"],
                    "deadline_status": deadline_info["deadline_status"],
                    "deadline_warning": deadline_info["deadline_warning"],
                }
            )

    return (
        jsonify(
            {
                "count": len(recommendations),
                "recommendations": recommendations,
            }
        ),
        200,
    )
