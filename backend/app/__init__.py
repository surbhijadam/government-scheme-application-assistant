import os

from dotenv import load_dotenv
from flask import Flask

from app.config import build_database_uri
from app.extensions import db
from app.routes.admin_applications import admin_applications_bp
from app.routes.admin_schemes import admin_schemes_bp
from app.routes.applications import applications_bp
from app.routes.assistant import assistant_bp
from app.routes.auth import auth_bp
from app.routes.documents import documents_bp
from app.routes.eligibility import eligibility_bp
from app.routes.health import health_bp
from app.routes.profile import profile_bp
from app.routes.recommendations import recommendations_bp
from app.routes.schemes import schemes_bp


def create_app():
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        from app import models  # noqa: F401  (registers models with SQLAlchemy)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(schemes_bp, url_prefix="/api")
    app.register_blueprint(eligibility_bp, url_prefix="/api")
    app.register_blueprint(recommendations_bp, url_prefix="/api")
    app.register_blueprint(applications_bp, url_prefix="/api")
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(admin_schemes_bp, url_prefix="/api")
    app.register_blueprint(admin_applications_bp, url_prefix="/api")
    app.register_blueprint(assistant_bp, url_prefix="/api")

    return app