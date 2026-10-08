"""Business logic for scheme application deadlines."""

from datetime import date


DEADLINE_STATUS_NOT_SPECIFIED = "not_specified"
DEADLINE_STATUS_UPCOMING = "upcoming"
DEADLINE_STATUS_APPROACHING = "approaching"
DEADLINE_STATUS_TODAY = "today"
DEADLINE_STATUS_PASSED = "passed"

DEADLINE_WARNING_DAYS = 7


def get_deadline_info(deadline):
    """
    Calculate deadline information dynamically.

    The deadline itself is stored in the database.
    All other values are calculated at runtime.
    """

    if deadline is None:
        return {
            "days_remaining": None,
            "deadline_status": DEADLINE_STATUS_NOT_SPECIFIED,
            "deadline_warning": False,
        }

    today = date.today()
    days_remaining = (deadline - today).days

    if days_remaining < 0:
        status = DEADLINE_STATUS_PASSED
        warning = False
    elif days_remaining == 0:
        status = DEADLINE_STATUS_TODAY
        warning = True
    elif days_remaining <= DEADLINE_WARNING_DAYS:
        status = DEADLINE_STATUS_APPROACHING
        warning = True
    else:
        status = DEADLINE_STATUS_UPCOMING
        warning = False

    return {
        "days_remaining": days_remaining,
        "deadline_status": status,
        "deadline_warning": warning,
    }