"""One-time script to create all tables in MySQL from the SQLAlchemy models."""
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    tables = db.inspect(db.engine).get_table_names()
    print("Tables now in the database:")
    for name in sorted(tables):
        print(f"  - {name}")