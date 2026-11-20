"""
CivicFix – Utility Helpers
Reusable functions and decorators used across the application.
"""

import os
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import abort, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Complaint


# ═══════════════════════════════════════════════════════════════════════
#  ROLE-BASED ACCESS DECORATORS
# ═══════════════════════════════════════════════════════════════════════

def admin_required(f):
    """Decorator: abort 403 unless the current user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def citizen_required(f):
    """Decorator: abort 403 unless the current user is a citizen."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_citizen:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════════════
#  COMPLAINT ID GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_complaint_id():
    """Generate a unique, human-readable complaint ID.

    Format: CF-YYYYMMDD-XXXX
    Example: CF-20261120-0003

    The counter resets each day and auto-increments.
    """
    today = datetime.now(timezone.utc).strftime('%Y%m%d')
    prefix = f'CF-{today}-'

    # Find the highest existing counter for today
    last = (
        Complaint.query
        .filter(Complaint.complaint_id.like(f'{prefix}%'))
        .order_by(Complaint.complaint_id.desc())
        .first()
    )

    if last:
        last_counter = int(last.complaint_id.split('-')[-1])
        new_counter = last_counter + 1
    else:
        new_counter = 1

    return f'{prefix}{new_counter:04d}'


# ═══════════════════════════════════════════════════════════════════════
#  IMAGE UPLOAD HELPERS
# ═══════════════════════════════════════════════════════════════════════

def allowed_file(filename):
    """Check whether the filename has an allowed image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_image(file, subfolder='complaints'):
    """Save an uploaded image file to disk with a safe, unique filename.

    Args:
        file: FileStorage object from the request.
        subfolder: 'complaints' or 'resolutions'.

    Returns:
        The saved filename (not the full path), or None if the file is
        invalid.
    """
    if file is None or file.filename == '':
        return None

    if not allowed_file(file.filename):
        return None

    # Build a unique filename to avoid collisions
    original = secure_filename(file.filename)
    ext = original.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'

    # Determine target directory
    if subfolder == 'resolutions':
        target_dir = current_app.config['RESOLUTION_UPLOAD_FOLDER']
    else:
        target_dir = current_app.config['COMPLAINT_UPLOAD_FOLDER']

    os.makedirs(target_dir, exist_ok=True)
    file.save(os.path.join(target_dir, unique_name))

    return unique_name
