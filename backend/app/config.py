import os

from sqlalchemy.engine import URL

REQUIRED_DB_VARIABLES = ("DB_USER", "DB_PASSWORD", "DB_NAME")


def build_database_uri():
    # The test suite (backend/tests/conftest.py) sets TEST_DATABASE_URI to an
    # in-memory SQLite database, so pytest never touches real MySQL data.
    # This is the ONLY way the database URI can be overridden - there is no
    # equivalent override for DB_PASSWORD or any other credential.
    test_override = os.getenv("TEST_DATABASE_URI")
    if test_override:
        return test_override

    missing = [name for name in REQUIRED_DB_VARIABLES if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Check your .env file."
        )

    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
        query={"charset": "utf8mb4"},
    )
    return url.render_as_string(hide_password=False)