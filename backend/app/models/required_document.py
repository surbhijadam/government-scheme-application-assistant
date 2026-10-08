from app.extensions import db


class RequiredDocument(db.Model):
    __tablename__ = "required_documents"

    document_id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(
        db.Integer, db.ForeignKey("schemes.scheme_id"), nullable=False
    )
    document_name = db.Column(db.String(150), nullable=False)
    mandatory = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<RequiredDocument {self.document_name}>"