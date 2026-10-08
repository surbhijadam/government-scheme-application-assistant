from flask import Blueprint, jsonify, request

from app.models import EligibilityRule, RequiredDocument, Scheme

from app.services.deadline import get_deadline_info

from app.extensions import db

schemes_bp = Blueprint("schemes", __name__)


@schemes_bp.route("/schemes", methods=["GET"])
def list_schemes():
    """List schemes, with optional search and category filtering."""
    query = Scheme.query.filter_by(status="active")

    search_term = request.args.get("search", "").strip()
    if search_term:
        query = query.filter(Scheme.name.ilike(f"%{search_term}%"))

    category = request.args.get("category", "").strip()
    if category:
        query = query.filter(Scheme.category.ilike(category))

    schemes = query.order_by(Scheme.name).all()

    return (
        jsonify(
            {
                "count": len(schemes),
                "schemes": [_serialize_scheme_summary(s) for s in schemes],
            }
        ),
        200,
    )


@schemes_bp.route("/schemes/<int:scheme_id>", methods=["GET"])
def get_scheme(scheme_id):
    """Return full details for a single scheme, including rules and documents."""
    scheme = db.session.get(Scheme, scheme_id)

    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    return jsonify(_serialize_scheme_detail(scheme)), 200


def _serialize_scheme_summary(scheme):
    deadline_info = get_deadline_info(scheme.deadline)

    return {
        "scheme_id": scheme.scheme_id,
        "name": scheme.name,
        "category": scheme.category,
        "description": scheme.description,
        "deadline": (
            scheme.deadline.isoformat()
            if scheme.deadline
            else None
        ),
        "days_remaining": deadline_info["days_remaining"],
        "deadline_status": deadline_info["deadline_status"],
        "deadline_warning": deadline_info["deadline_warning"],
    }


def _serialize_scheme_detail(scheme):
    deadline_info = get_deadline_info(scheme.deadline)

    return {
        "scheme_id": scheme.scheme_id,
        "name": scheme.name,
        "description": scheme.description,
        "benefits": scheme.benefits,
        "category": scheme.category,
        "application_url": scheme.application_url,
        "status": scheme.status,
        "deadline": (
            scheme.deadline.isoformat()
            if scheme.deadline
            else None
        ),
        "days_remaining": deadline_info["days_remaining"],
        "deadline_status": deadline_info["deadline_status"],
        "deadline_warning": deadline_info["deadline_warning"],
        "eligibility_rules": [
            {
                "rule_id": rule.rule_id,
                "field_name": rule.field_name,
                "operator": rule.operator,
                "expected_value": rule.expected_value,
            }
            for rule in scheme.eligibility_rules
        ],
        "required_documents": [
            {
                "document_id": doc.document_id,
                "document_name": doc.document_name,
                "mandatory": doc.mandatory,
            }
            for doc in scheme.required_documents
        ],
    }