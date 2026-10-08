"""
One-time utility to promote an existing user to the 'admin' role.

This is intentionally a script you run by hand, not an API endpoint -
there must be no way for a regular user to make themselves an admin
through the running application.

Usage:
    python promote_admin.py someone@example.com
"""
import sys

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()


def promote(email):
    with app.app_context():
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            print(f"No user found with email '{email}'")
            return

        if user.role == "admin":
            print(f"{user.email} is already an admin.")
            return

        user.role = "admin"
        db.session.commit()
        print(f"{user.email} is now an admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python promote_admin.py <email>")
        sys.exit(1)

    promote(sys.argv[1])