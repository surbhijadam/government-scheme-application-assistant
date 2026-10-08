from datetime import datetime

from app.extensions import db


class ApplicationDocument(db.Model):
    """A file the applicant uploaded to satisfy one of a scheme's required documents."""

    __tablename__ = "application_documents"

    application_document_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.application_id"), nullable=False
    )
    document_id = db.Column(
        db.Integer, db.ForeignKey("required_documents.document_id"), nullable=False
    )
    stored_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ApplicationDocument app={self.application_id} doc={self.document_id}>"