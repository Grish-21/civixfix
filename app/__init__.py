"""
CivicFix – Application Factory
Creates and configures the Flask application instance.
"""

import os
from flask import Flask, render_template
from config import Config


def create_app(config_class=Config):
    """Application factory – creates, configures and returns the Flask app."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config.get('COMPLAINT_UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('RESOLUTION_UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # ── Initialise extensions ─────────────────────────────────────────
    from app.extensions import db, login_manager, csrf

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login user loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Register blueprints ───────────────────────────────────────────
    from app.auth import auth_bp
    from app.main import main_bp
    from app.citizen import citizen_bp
    from app.admin import admin_bp
    from app.complaints import complaints_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(complaints_bp)

    # ── Error handlers ────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template('errors/413.html'), 413

    # ── Context processors ────────────────────────────────────────────
    @app.context_processor
    def inject_now():
        """Make current year available in all templates for the footer."""
        from datetime import datetime, timezone
        return {'now': datetime.now(timezone.utc)}

    # ── Create database tables & seed data ────────────────────────────
    with app.app_context():
        # Enable SQLite foreign key enforcement
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, 'connect')
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

        db.create_all()

        from app.seed import seed_database
        seed_database()

    return app
