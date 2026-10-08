"""
Decides whether an application is complete enough to submit.

Returns a list of blocking reasons - an empty list means the application
can be submitted.
"""
from app.services.eligibility_engine import check_eligibility


def get_submission_blockers(application, profile):
    """Return a list of reasons this application cannot be submitted yet."""
    blockers = []

    if not profile:
        blockers.append("Your profile is incomplete. Fill it in at PUT /api/profile.")
        return blockers  # no point checking eligibility without a profile

    profile_data = {
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "income": float(profile.income) if profile.income is not None else None,
        "occupation": profile.occupation,
        "category": profile.category,
    }

    scheme = application.scheme
    rules = [
        {
            "field_name": rule.field_name,
            "operator": rule.operator,
            "expected_value": rule.expected_value,
        }
        for rule in scheme.eligibility_rules
    ]

    eligibility_result = check_eligibility(profile_data, rules)
    if not eligibility_result["eligible"]:
        for failed_rule in eligibility_result["failed_rules"]:
            blockers.append(failed_rule["reason"])

    uploaded_document_ids = {doc.document_id for doc in application.documents}
    for required_document in scheme.required_documents:
        if required_document.mandatory and required_document.document_id not in uploaded_document_ids:
            blockers.append(f"Missing required document: {required_document.document_name}")

    return blockers