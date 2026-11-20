"""
CivicFix – Citizen Routes
Dashboard, complaint list, and profile management for citizen users.
"""

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.citizen import citizen_bp
from app.extensions import db
from app.models import Complaint, COMPLAINT_CATEGORIES, COMPLAINT_STATUSES
from app.utils import citizen_required


@citizen_bp.route('/dashboard')
@login_required
@citizen_required
def dashboard():
    """Citizen dashboard with complaint statistics and recent complaints."""
    user_complaints = Complaint.query.filter_by(user_id=current_user.id)

    stats = {
        'total': user_complaints.count(),
        'pending': user_complaints.filter(
            Complaint.status.in_(['Submitted', 'Under Review'])
        ).count(),
        'in_progress': user_complaints.filter(
            Complaint.status.in_(['Verified', 'Assigned', 'In Progress'])
        ).count(),
        'resolved': user_complaints.filter_by(status='Resolved').count(),
        'rejected': user_complaints.filter_by(status='Rejected').count(),
    }

    recent_complaints = (
        Complaint.query
        .filter_by(user_id=current_user.id)
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'citizen/dashboard.html',
        stats=stats,
        recent_complaints=recent_complaints,
    )


@citizen_bp.route('/complaints')
@login_required
@citizen_required
def my_complaints():
    """Paginated list of citizen's complaints with search and filter."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status = request.args.get('status', '', type=str)
    category = request.args.get('category', '', type=str)
    per_page = current_app.config.get('COMPLAINTS_PER_PAGE', 10)

    query = Complaint.query.filter_by(user_id=current_user.id)

    # Apply filters
    if search:
        query = query.filter(
            (Complaint.complaint_id.ilike(f'%{search}%')) |
            (Complaint.title.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)

    complaints = (
        query
        .order_by(Complaint.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        'citizen/my_complaints.html',
        complaints=complaints,
        search=search,
        status=status,
        category=category,
        COMPLAINT_CATEGORIES=COMPLAINT_CATEGORIES,
        COMPLAINT_STATUSES=COMPLAINT_STATUSES,
    )


@citizen_bp.route('/profile')
@login_required
@citizen_required
def profile():
    """Citizen profile page."""
    return render_template('citizen/profile.html')


@citizen_bp.route('/profile/update', methods=['POST'])
@login_required
@citizen_required
def update_profile():
    """Update citizen profile information."""
    full_name = request.form.get('full_name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    address = request.form.get('address', '').strip()

    errors = []
    if not full_name or len(full_name) < 2:
        errors.append('Full name must be at least 2 characters.')
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        errors.append('Please enter a valid 10-digit mobile number.')
    if not address or len(address) < 5:
        errors.append('Address must be at least 5 characters.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('citizen.profile'))

    try:
        current_user.full_name = full_name
        current_user.mobile = mobile
        current_user.address = address
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while updating your profile.', 'danger')

    return redirect(url_for('citizen.profile'))
