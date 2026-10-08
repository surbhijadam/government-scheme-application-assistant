"""
Defines which status transitions an admin may perform.

STATUS_ORDER (Phase 10) describes the typical forward *path* an application
follows for display purposes, but the real review workflow branches: from
"under_review", an admin can approve, reject, OR ask for more info - these
are siblings, not a strict next-step-only chain. So the transition map is
defined explicitly here, using the same named constants as STATUS_ORDER,
rather than mechanically derived from the list order.
"""
from app.utils.status_flow import (
    STATUS_ADDITIONAL_INFO_REQUIRED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
    STATUS_UNDER_REVIEW,
)

ALLOWED_TRANSITIONS = {
    # "draft" is deliberately absent: an admin should never touch an
    # application the user hasn't submitted yet.
    STATUS_SUBMITTED: {STATUS_UNDER_REVIEW},
    STATUS_UNDER_REVIEW: {STATUS_ADDITIONAL_INFO_REQUIRED, STATUS_APPROVED, STATUS_REJECTED},
    STATUS_ADDITIONAL_INFO_REQUIRED: {STATUS_UNDER_REVIEW, STATUS_APPROVED, STATUS_REJECTED},
}


def get_allowed_next_statuses(current_status):
    """Return the set of statuses an admin may move this application to next."""
    return ALLOWED_TRANSITIONS.get(current_status, set())