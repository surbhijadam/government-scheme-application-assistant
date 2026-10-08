import os
import uuid

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Application, ApplicationDocument, RequiredDocument
from app.utils.decorators import login_required
from app.utils.file_validation import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    get_extension,
    get_file_size,
    is_allowed_extension,
)

documents_bp = Blueprint("documents", __name__)


def _get_owned_application(application_id):
    return Application.query.filter_by(
        application_id=application_id, user_id=g.current_user_id
    ).first()


@documents_bp.route("/applications/<int:application_id>/documents", methods=["POST"])
@login_required
def upload_document(application_id):
    """Upload a dummy/demo document to satisfy one of a scheme's required documents."""
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    if application.status != "draft":
        return (
            jsonify({"error": f"Documents can only be added while the application is a draft (current status: '{application.status}')"}),
            409,
        )

    document_id = request.form.get("document_id")
    if not document_id:
        return jsonify({"error": "document_id is required (form field)"}), 400

    required_document = RequiredDocument.query.filter_by(
        document_id=document_id, scheme_id=application.scheme_id
    ).first()
    if not required_document:
        return jsonify({"error": "That document_id is not required for this scheme"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded (expected form field 'file')"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No file was selected"}), 400

    if not is_allowed_extension(uploaded_file.filename):
        return (
            jsonify({"error": f"File type not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}),
            400,
        )

    file_size = get_file_size(uploaded_file)
    if file_size > MAX_FILE_SIZE_BYTES:
        return (
            jsonify({"error": f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"}),
            400,
        )
    if file_size == 0:
        return jsonify({"error": "Uploaded file is empty"}), 400

    # Replace any existing upload for this same required document on this application
    existing = ApplicationDocument.query.filter_by(
        application_id=application.application_id, document_id=required_document.document_id
    ).first()

    upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(application.application_id))
    os.makedirs(upload_folder, exist_ok=True)

    uploaded_filename = uploaded_file.filename or ""
    safe_original_name = secure_filename(uploaded_filename)
    stored_filename = f"{uuid.uuid4().hex}.{get_extension(safe_original_name)}"
    destination_path = os.path.join(upload_folder, stored_filename)
    uploaded_file.save(destination_path)

    if existing:
        old_path = os.path.join(upload_folder, existing.stored_filename)
        if os.path.exists(old_path):
            os.remove(old_path)
        existing.stored_filename = stored_filename
        existing.original_filename = safe_original_name
        existing.file_size_bytes = file_size
        existing.content_type = uploaded_file.content_type or "application/octet-stream"
        document_record = existing
    else:
        document_record = ApplicationDocument(
            application_id=application.application_id,  #type: ignore
            document_id=required_document.document_id,  #type: ignore
            stored_filename=stored_filename,  #type: ignore
            original_filename=safe_original_name, #type: ignore
            file_size_bytes=file_size,  #type: ignore
            content_type=uploaded_file.content_type or "application/octet-stream",  #type: ignore
        )
        db.session.add(document_record)

    db.session.commit()

    return jsonify(_serialize_document(document_record, required_document)), 201


@documents_bp.route("/applications/<int:application_id>/documents", methods=["GET"])
@login_required
def list_documents(application_id):
    """List required documents for this application's scheme, and what's been uploaded."""
    application = _get_owned_application(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    uploaded_by_doc_id = {
        doc.document_id: doc for doc in application.documents
    }

    required_documents = application.scheme.required_documents

    checklist = []
    for required_document in required_documents:
        uploaded = uploaded_by_doc_id.get(required_document.document_id)
        checklist.append(
            {
                "document_id": required_document.document_id,
                "document_name": required_document.document_name,
                "mandatory": required_document.mandatory,
                "uploaded": uploaded is not None,
                "file": _serialize_document(uploaded, required_document) if uploaded else None,
            }
        )

    return jsonify({"checklist": checklist}), 200


def _serialize_document(document_record, required_document):
    if document_record is None:
        return None
    return {
        "application_document_id": document_record.application_document_id,
        "document_id": required_document.document_id,
        "document_name": required_document.document_name,
        "original_filename": document_record.original_filename,
        "file_size_bytes": document_record.file_size_bytes,
        "content_type": document_record.content_type,
        "uploaded_at": document_record.uploaded_at.isoformat() if document_record.uploaded_at else None,
    }