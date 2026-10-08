"""Add deadline column to schemes table."""

import sys
from pathlib import Path

from sqlalchemy import inspect, text


# Add the backend directory to Python's import path.
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.extensions import db


app = create_app()


with app.app_context():
    inspector = inspect(db.engine)

    if "schemes" not in inspector.get_table_names():
        raise RuntimeError(
            "The 'schemes' table does not exist. "
            "Run the existing database setup first."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns("schemes")
    }

    if "deadline" in columns:
        print("Column 'deadline' already exists. Nothing to do.")
    else:
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE schemes "
                    "ADD COLUMN deadline DATE NULL"
                )
            )

        print("Added 'deadline' DATE NULL to schemes.")