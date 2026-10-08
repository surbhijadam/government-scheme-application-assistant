from flask import Blueprint, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Tell the caller that the API is alive."""
    return jsonify({"message": "Government Scheme Assistant API is running"}), 200


@health_bp.route("/health/db", methods=["GET"])
def database_health_check():
    """Check that Flask can talk to MySQL."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"message": "Database connection successful"}), 200
    except SQLAlchemyError:
        current_app.logger.exception("Database health check failed")
        return jsonify({"message": "Database connection failed"}), 503