from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship(
        "UserProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    applications = db.relationship(
        "Application", backref="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.user_id} {self.email}>"