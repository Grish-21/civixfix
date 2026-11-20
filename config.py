"""
CivicFix Configuration
Centralised Flask configuration for the application.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class."""

    # ── Security ──────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('CIVICFIX_SECRET_KEY', 'civicfix-dev-secret-key-change-in-production')

    # ── Database ──────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'civicfix.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── File Uploads ──────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    COMPLAINT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'complaints')
    RESOLUTION_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'resolutions')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # ── Pagination ────────────────────────────────────────────────────
    COMPLAINTS_PER_PAGE = 10

    # ── Session ───────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
