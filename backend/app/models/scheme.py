from app.extensions import db


class Scheme(db.Model):
    __tablename__ = "schemes"

    scheme_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    benefits = db.Column(db.Text)
    category = db.Column(db.String(100))
    application_url = db.Column(db.String(255))
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")

    eligibility_rules = db.relationship(
        "EligibilityRule", backref="scheme", cascade="all, delete-orphan"
    )
    required_documents = db.relationship(
        "RequiredDocument", backref="scheme", cascade="all, delete-orphan"
    )
    applications = db.relationship(
        "Application", backref="scheme", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Scheme {self.scheme_id} {self.name}>"