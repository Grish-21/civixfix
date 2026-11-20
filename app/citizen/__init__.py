"""Citizen blueprint – citizen dashboard, profile."""
from flask import Blueprint

citizen_bp = Blueprint('citizen', __name__, url_prefix='/citizen')

from app.citizen import routes  # noqa: E402, F401
