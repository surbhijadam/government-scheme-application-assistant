from app.extensions import db


class Application(db.Model):
    __tablename__ = "applications"

    application_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    scheme_id = db.Column(
        db.Integer, db.ForeignKey("schemes.scheme_id"), nullable=False
    )
    status = db.Column(db.String(30), nullable=False, default="draft")
    submitted_at = db.Column(db.DateTime, nullable=True)

    status_history = db.relationship(
        "ApplicationStatusHistory",
        backref="application",
        cascade="all, delete-orphan",
    )
    documents = db.relationship(
        "ApplicationDocument", backref="application", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Application {self.application_id} status={self.status}>"