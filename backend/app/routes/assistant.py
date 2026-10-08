from flask import Blueprint, jsonify, request

from app.models import Scheme
from app.services.ai_assistant import ask_assistant, build_scheme_context
from app.utils.decorators import login_required
from app.extensions import db

assistant_bp = Blueprint("assistant", __name__)


@assistant_bp.route("/assistant/chat", methods=["POST"])
@login_required
def chat():
    """
    Ask the AI assistant a question, optionally about a specific scheme.

    The assistant never receives the user's profile data - only verified
    scheme information - and it never makes eligibility decisions; that
    stays with the deterministic engine used elsewhere in the project.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    scheme_id = data.get("scheme_id")

    if not message:
        return jsonify({"error": "message is required"}), 400

    scheme_context = None
    scheme_name = None

    if scheme_id:
        scheme = db.session.get(Scheme, scheme_id)        
        if not scheme:
            return jsonify({"error": "Scheme not found"}), 404
        scheme_context = build_scheme_context(scheme)
        scheme_name = scheme.name

    reply, error = ask_assistant(message, scheme_context=scheme_context)

    if error:
        return jsonify({"error": error}), 503

    return (
        jsonify(
            {
                "reply": reply,
                "scheme_context_used": scheme_name,
                "disclaimer": "This is an AI assistant for a demo project, not an official "
                "government authority. It does not make eligibility decisions.",
            }
        ),
        200,
    )