from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import EligibilityRule, RequiredDocument, Scheme
from app.services.eligibility_engine import OPERATORS
from app.utils.decorators import admin_required
from datetime import date
from app.services.deadline import get_deadline_info


def _parse_deadline(value):
    """
    Parse an optional ISO date string into a Python date.

    Returns:
        date object when a valid date is supplied
        None when the value is empty/null

    Raises:
        ValueError for an invalid date.
    """
    if value is None or value == "":
        return None

    if not isinstance(value, str):
        raise ValueError("deadline must be in YYYY-MM-DD format")

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("deadline must be in YYYY-MM-DD format")


admin_schemes_bp = Blueprint("admin_schemes", __name__)


@admin_schemes_bp.route("/admin/schemes", methods=["POST"])
@admin_required
def create_scheme():
    """Create a new scheme."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400

    try:
        deadline = _parse_deadline(data.get("deadline"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    scheme = Scheme(
        name=name, #type: ignore
        description=data.get("description"), #type: ignore
        benefits=data.get("benefits"), #type: ignore
        category=data.get("category"), #type: ignore
        application_url=data.get("application_url"), #type: ignore
        deadline=deadline, #type: ignore
        status=data.get("status", "active"), #type: ignore
    )
    scheme.description = data.get("description")

    db.session.add(scheme)
    db.session.commit()

    return jsonify(_serialize_scheme(scheme)), 201


@admin_schemes_bp.route("/admin/schemes/<int:scheme_id>", methods=["PUT"])
@admin_required
def update_scheme(scheme_id):
    """Update an existing scheme's fields (e.g. to activate/deactivate it)."""
    scheme = Scheme.query.get(scheme_id)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    data = request.get_json(silent=True) or {}

    if "status" in data and data["status"] not in ("active", "inactive"):
        return jsonify({"error": "status must be 'active' or 'inactive'"}), 400

    for field in (
        "name",
        "description",
        "benefits",
        "category",
        "application_url",
        "status",
    ):
        if field in data:
            setattr(scheme, field, data[field])

    if "deadline" in data:
        try:
            scheme.deadline = _parse_deadline(data["deadline"])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    db.session.commit()
    return jsonify(_serialize_scheme(scheme)), 200


@admin_schemes_bp.route("/admin/schemes/<int:scheme_id>/rules", methods=["POST"])
@admin_required
def add_eligibility_rule(scheme_id):
    """Add an eligibility rule to a scheme."""
    scheme = Scheme.query.get(scheme_id)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    data = request.get_json(silent=True) or {}
    field_name = (data.get("field_name") or "").strip()
    op_symbol = (data.get("operator") or "").strip()
    expected_value = data.get("expected_value")

    if not field_name:
        return jsonify({"error": "field_name is required"}), 400
    if op_symbol not in OPERATORS:
        return jsonify({"error": f"operator must be one of: {', '.join(sorted(OPERATORS))}"}), 400
    if expected_value is None or str(expected_value).strip() == "":
        return jsonify({"error": "expected_value is required"}), 400

    rule = EligibilityRule(
        scheme_id=scheme.scheme_id,  # type: ignore
        field_name=field_name,  # type: ignore
        operator=op_symbol,  # type: ignore
        expected_value=str(expected_value),  # type: ignore
    )
    db.session.add(rule)
    db.session.commit()

    return jsonify(_serialize_rule(rule)), 201


@admin_schemes_bp.route("/admin/schemes/<int:scheme_id>/rules/<int:rule_id>", methods=["DELETE"])
@admin_required
def delete_eligibility_rule(scheme_id, rule_id):
    """Remove an eligibility rule from a scheme."""
    rule = EligibilityRule.query.filter_by(rule_id=rule_id, scheme_id=scheme_id).first()
    if not rule:
        return jsonify({"error": "Rule not found for this scheme"}), 404

    db.session.delete(rule)
    db.session.commit()
    return jsonify({"message": "Rule deleted"}), 200


@admin_schemes_bp.route("/admin/schemes/<int:scheme_id>/documents", methods=["POST"])
@admin_required
def add_required_document(scheme_id):
    """Add a required document definition to a scheme."""
    scheme = Scheme.query.get(scheme_id)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    data = request.get_json(silent=True) or {}
    document_name = (data.get("document_name") or "").strip()

    if not document_name:
        return jsonify({"error": "document_name is required"}), 400

    document = RequiredDocument(
        **{
            "scheme_id": scheme.scheme_id,
            "document_name": document_name,
            "mandatory": bool(data.get("mandatory", True)),
        }
    )
    db.session.add(document)
    db.session.commit()

    return jsonify(_serialize_document(document)), 201


@admin_schemes_bp.route("/admin/schemes/<int:scheme_id>/documents/<int:document_id>", methods=["DELETE"])
@admin_required
def delete_required_document(scheme_id, document_id):
    """Remove a required document definition from a scheme."""
    document = RequiredDocument.query.filter_by(document_id=document_id, scheme_id=scheme_id).first()
    if not document:
        return jsonify({"error": "Document not found for this scheme"}), 404

    db.session.delete(document)
    db.session.commit()
    return jsonify({"message": "Document requirement deleted"}), 200


def _serialize_scheme(scheme):
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
        **deadline_info,
    }

def _serialize_rule(rule):
    return {
        "rule_id": rule.rule_id,
        "scheme_id": rule.scheme_id,
        "field_name": getattr(rule, "field_name", getattr(rule, "field", None)),
        "operator": rule.operator,
        "expected_value": getattr(rule, "expected_value", getattr(rule, "value", None)),
    }


def _serialize_document(document):
    return {
        "document_id": document.document_id,
        "scheme_id": document.scheme_id,
        "document_name": document.document_name,
        "mandatory": document.mandatory,
    }