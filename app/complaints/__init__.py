"""Complaints blueprint – submit, track, detail, feedback."""
from flask import Blueprint

complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')

from app.complaints import routes  # noqa: E402, F401
