from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app.services.deadline import get_deadline_info

from app.extensions import db
from app.models import Application, ApplicationStatusHistory, Scheme, UserProfile
from app.services.application_validator import get_submission_blockers
from app.utils.decorators import login_required
from app.utils.status_flow import (
    STATUS_ADDITIONAL_INFO_REQUIRED,
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_WITHDRAWN,
)

applications_bp = Blueprint("applications", __name__)

# Active (non-final) statuses. A user may only have one non-final
# application per scheme at a time, to avoid duplicate applications.
ACTIVE_STATUSES = {STATUS_DRAFT, STATUS_SUBMITTED, STATUS_UNDER_REVIEW, STATUS_ADDITIONAL_INFO_REQUIRED}

# A user may withdraw their OWN application only while it is still a draft.
# Anything further along is managed by admin status updates (Phase 11).
WITHDRAWABLE_STATUSES = {STATUS_DRAFT}


@applications_bp.route("/applications", methods=["POST"])
@login_required
def create_application():
    """Start a new (draft) application for a scheme."""
    data = request.get_json(silent=True) or {}
    scheme_id = data.get("scheme_id")

    if not scheme_id:
        return jsonify({"error": "scheme_id is required"}), 400

    scheme = Scheme.query.get(scheme_id)
   
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    deadline_info = get_deadline_info(scheme.deadline)

    if deadline_info["deadline_status"] == "passed":
        return jsonify({
            "error": "Application deadline has passed."
        }), 400

    existing = Application.query.filter(
        Application.user_id == g.current_user_id,
        Application.scheme_id == scheme_id,
        Application.status.in_(ACTIVE_STATUSES),
    ).first()
    if existing:
        return (
            jsonify(
                {
                    "error": "You already have an active application for this scheme",
                    "application_id": existing.application_id,
                    "status": existing.status,
                }
            ),
            409,
        )

    application = Application(
        user_id=g.current_user_id,  #type: ignore
        scheme_id=scheme_id,  #type: ignore
        status=STATUS_DRAFT,  #type: ignore
    )
    db.session.add(application)
    db.session.commit()

    status_history = ApplicationStatusHistory()
    status_history.status = STATUS_DRAFT
    status_history.remarks = "Application created"
    status_history.application_id = application.application_id
    db.session.add(status_history)
    db.session.commit()

    return jsonify(_serialize_application(application)), 201


@applications_bp.route("/applications", methods=["GET"])
@login_required
def list_applications():
    """List all of the logged-in user's applications, newest first."""
    applications = (
        Application.query.filter_by(user_id=g.current_user_id)
        .order_by(Application.application_id.desc())
        .all()
    )
    return (
        jsonify(
            {
                "count": len(applications),
                "applications": [_serialize_application(a) for a in applications],
            }
        ),
        200,
    )


@applications_bp.route("/applications/<int:application_id>", methods=["GET"])
@login_required
def get_application(application_id):
    """Get one application, including its scheme name and status history."""
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    return jsonify(_serialize_application(application, include_history=True)), 200


@applications_bp.route("/applications/<int:application_id>", methods=["PUT"])
@login_required
def update_application(application_id):
    """
    Update a draft application.

    The current schema stores no separate form fields on an application -
    eligibility data lives in the user's profile, and documents live in
    Phase 9's upload feature. The one action available here is withdrawing
    a draft before it's submitted.
    """
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status != STATUS_WITHDRAWN:
        return (
            jsonify({"error": "The only supported update is {'status': 'withdrawn'}"}),
            400,
        )

    if application.status not in WITHDRAWABLE_STATUSES:
        return (
            jsonify({"error": f"Cannot withdraw an application with status '{application.status}'"}),
            409,
        )

    application.status = STATUS_WITHDRAWN
    status_history = ApplicationStatusHistory()
    status_history.status = STATUS_WITHDRAWN
    status_history.remarks = "Withdrawn by applicant"
    status_history.application_id = application.application_id
    db.session.add(status_history)
    db.session.commit()

    return jsonify(_serialize_application(application)), 200


@applications_bp.route("/applications/<int:application_id>/submit", methods=["POST"])
@login_required
def submit_application(application_id):
    """Submit a draft application, after validating it is complete."""
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    if application.status != STATUS_DRAFT:
        return (
            jsonify({"error": f"Only a draft application can be submitted (current status: '{application.status}')"}),
            409,
        )

    deadline_info = get_deadline_info(application.scheme.deadline)

    if deadline_info["deadline_status"] == "passed":
        return jsonify({
            "error": "Application deadline has passed."
        }), 400

    profile = UserProfile.query.filter_by(user_id=g.current_user_id).first()
    blockers = get_submission_blockers(application, profile)

    if blockers:
        return (
            jsonify(
                {
                    "error": "Application is incomplete and cannot be submitted",
                    "blockers": blockers,
                }
            ),
            400,
        )

    application.status = STATUS_SUBMITTED
    application.submitted_at = datetime.now(timezone.utc)
    status_history = ApplicationStatusHistory()
    status_history.status = STATUS_SUBMITTED
    status_history.remarks = "Submitted by applicant"
    status_history.application_id = application.application_id
    db.session.add(status_history)
    db.session.commit()

    return jsonify(_serialize_application(application)), 200


@applications_bp.route("/applications/<int:application_id>/status", methods=["GET"])
@login_required
def get_application_status(application_id):
    """Return the current status and full status history for one application."""
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    history = sorted(application.status_history, key=lambda h: h.history_id)

    return (
        jsonify(
            {
                "application_id": application.application_id,
                "scheme_id": application.scheme_id,
                "scheme_name": application.scheme.name,
                "current_status": application.status,
                "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
                "status_history": [
                    {
                        "status": h.status,
                        "remarks": h.remarks,
                        "updated_at": h.updated_at.isoformat() if h.updated_at else None,
                    }
                    for h in history
                ],
            }
        ),
        200,
    )


def _get_owned_application(application_id):
    """Fetch an application only if it belongs to the logged-in user."""
    return Application.query.filter_by(
        application_id=application_id, user_id=g.current_user_id
    ).first()


def _serialize_application(application, include_history=False):
    data = {
        "application_id": application.application_id,
        "scheme_id": application.scheme_id,
        "scheme_name": application.scheme.name,
        "status": application.status,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
    }
    if include_history:
        data["status_history"] = [
            {
                "status": h.status,
                "remarks": h.remarks,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            }
            for h in sorted(application.status_history, key=lambda h: h.history_id)
        ]
    return data