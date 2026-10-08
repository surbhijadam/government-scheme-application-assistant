from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Application, ApplicationStatusHistory
from app.services.status_transitions import get_allowed_next_statuses
from app.utils.decorators import admin_required
from app.utils.status_flow import ALL_STATUSES, FINAL_STATUSES

admin_applications_bp = Blueprint("admin_applications", __name__)


@admin_applications_bp.route("/admin/applications", methods=["GET"])
@admin_required
def list_all_applications():
    """List every application in the system, optionally filtered by status."""
    query = Application.query

    status_filter = request.args.get("status", "").strip()
    if status_filter:
        if status_filter not in ALL_STATUSES:
            return jsonify({"error": f"status must be one of: {', '.join(sorted(ALL_STATUSES))}"}), 400
        query = query.filter_by(status=status_filter)

    applications = query.order_by(Application.application_id.desc()).all()

    return (
        jsonify(
            {
                "count": len(applications),
                "applications": [_serialize_application_for_admin(a) for a in applications],
            }
        ),
        200,
    )


@admin_applications_bp.route("/admin/applications/<int:application_id>/status", methods=["PUT"])
@admin_required
def update_application_status(application_id):
    """Move an application to a new status, enforcing a valid transition."""
    application = db.session.get(Application, application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    remarks = (data.get("remarks") or "").strip() or "Status updated by admin"

    if new_status not in ALL_STATUSES:
        return jsonify({"error": f"status must be one of: {', '.join(sorted(ALL_STATUSES))}"}), 400

    current_status = application.status

    if current_status in FINAL_STATUSES:
        return (
            jsonify({"error": f"Cannot change status of an application that is already '{current_status}'"}),
            409,
        )

    allowed_next = get_allowed_next_statuses(current_status)
    if new_status not in allowed_next:
        return (
            jsonify(
                {
                    "error": f"Cannot move from '{current_status}' to '{new_status}'",
                    "allowed_next_statuses": sorted(allowed_next),
                }
            ),
            400,
        )

    application.status = new_status
    db.session.add(
        ApplicationStatusHistory(
            application_id=application.application_id, #type: ignore
            status=new_status, #type: ignore
            remarks=remarks, #type: ignore
        )
    )
    db.session.commit()

    return (
        jsonify(
            {
                **_serialize_application_for_admin(application),
                "allowed_next_statuses": sorted(get_allowed_next_statuses(new_status)),
            }
        ),
        200,
    )


def _serialize_application_for_admin(application):
    return {
        "application_id": application.application_id,
        "scheme_id": application.scheme_id,
        "scheme_name": application.scheme.name,
        "user_id": application.user_id,
        "applicant_name": application.user.name,
        "applicant_email": application.user.email,
        "status": application.status,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
    }