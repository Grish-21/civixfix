
"""
CivicFix Configuration
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # Security
    SECRET_KEY = os.environ.get(
        'CIVICFIX_SECRET_KEY',
        'civicfix-dev-secret-key-change-in-production'
    )

    # Persistent data directory
    DATA_DIR = os.environ.get(
        'CIVICFIX_DATA_DIR',
        os.path.join(BASE_DIR, 'instance')
    )

    # SQLite database
    SQLALCHEMY_DATABASE_URI = (
        'sqlite:///' + os.path.join(DATA_DIR, 'civicfix.db')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Image uploads
    UPLOAD_FOLDER = os.environ.get(
        'CIVICFIX_UPLOAD_DIR',
        os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    )

    COMPLAINT_UPLOAD_FOLDER = os.path.join(
        UPLOAD_FOLDER, 'complaints'
    )

    RESOLUTION_UPLOAD_FOLDER = os.path.join(
        UPLOAD_FOLDER, 'resolutions'
    )

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # Pagination
    COMPLAINTS_PER_PAGE = 10

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
