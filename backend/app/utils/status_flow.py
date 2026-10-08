"""
The application status flow, from SRS Appendix B:

    Draft -> Submitted -> Under Review -> Additional Information Required
          -> Approved / Rejected

"withdrawn" is a special status a user can reach from "draft" only (Phase 8).
Everything past "submitted" is set by an admin (Phase 11), not by the user.
"""

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_UNDER_REVIEW = "under_review"
STATUS_ADDITIONAL_INFO_REQUIRED = "additional_info_required"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_WITHDRAWN = "withdrawn"

# The main forward-moving flow, in order. Used for display and, in Phase 11,
# to validate that an admin can't skip steps backwards illogically.
STATUS_ORDER = [
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
    STATUS_ADDITIONAL_INFO_REQUIRED,
    STATUS_APPROVED,  # or STATUS_REJECTED, a terminal branch from any review stage
]

ALL_STATUSES = STATUS_ORDER + [STATUS_REJECTED, STATUS_WITHDRAWN]

FINAL_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_WITHDRAWN}