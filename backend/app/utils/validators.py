import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    """Return True if the string looks like a valid email address."""
    return bool(email) and bool(EMAIL_PATTERN.match(email))


def is_valid_password(password):
    """Return True if the password meets our minimum strength rule."""
    return bool(password) and len(password) >= 8