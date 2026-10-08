from app.extensions import db


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True
    )
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    state = db.Column(db.String(100))
    income = db.Column(db.Numeric(12, 2))
    occupation = db.Column(db.String(100))
    category = db.Column(db.String(50))
    other_details = db.Column(db.Text)

    def __repr__(self):
        return f"<UserProfile {self.profile_id} user={self.user_id}>"