from datetime import datetime

from app.extensions import db


class ApplicationStatusHistory(db.Model):
    __tablename__ = "application_status_history"

    history_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.application_id"), nullable=False
    )
    status = db.Column(db.String(30), nullable=False)
    remarks = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StatusHistory app={self.application_id} status={self.status}>"