from app.extensions import db


class EligibilityRule(db.Model):
    __tablename__ = "eligibility_rules"

    rule_id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(
        db.Integer, db.ForeignKey("schemes.scheme_id"), nullable=False
    )
    field_name = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(10), nullable=False)
    expected_value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<EligibilityRule {self.field_name} {self.operator} {self.expected_value}>"