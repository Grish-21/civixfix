"""
CivicFix – Complaint Routes
Submit, track, view details, and feedback for complaints.
"""

from flask import (
    render_template, redirect, url_for, flash, request, abort, current_app,
)
from flask_login import login_required, current_user

from app.complaints import complaints_bp
from app.extensions import db
from app.models import (
    Complaint, ComplaintStatusHistory, Feedback, Department,
    COMPLAINT_CATEGORIES, CATEGORY_DEPARTMENT_MAP,
)
from app.utils import citizen_required, generate_complaint_id, save_uploaded_image


# ═══════════════════════════════════════════════════════════════════════
#  SUBMIT A NEW COMPLAINT
# ═══════════════════════════════════════════════════════════════════════

@complaints_bp.route('/submit', methods=['GET', 'POST'])
@login_required
@citizen_required
def submit():
    """Submit a new civic complaint."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        area = request.form.get('area', '').strip()
        landmark = request.form.get('landmark', '').strip()
        image = request.files.get('image')

        # ── Server-side validation ────────────────────────────────────
        errors = []
        if not title:
            errors.append('Complaint title is required.')
        if not category or category not in COMPLAINT_CATEGORIES:
            errors.append('Please select a valid category.')
        if not description:
            errors.append('Description is required.')
        if not address:
            errors.append('Address is required.')
        if not area:
            errors.append('Area / Locality is required.')

        # Validate image if provided
        image_filename = None
        if image and image.filename:
            image_filename = save_uploaded_image(image, 'complaints')
            if image_filename is None:
                errors.append('Invalid image file. Only JPG, JPEG, and PNG files under 5 MB are accepted.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'complaints/submit.html',
                categories=COMPLAINT_CATEGORIES,
            )

        # ── Create the complaint ──────────────────────────────────────
        try:
            cid = generate_complaint_id()

            # Auto-assign department based on category
            dept_name = CATEGORY_DEPARTMENT_MAP.get(category)
            department = Department.query.filter_by(department_name=dept_name).first() if dept_name else None

            complaint = Complaint(
                complaint_id=cid,
                user_id=current_user.id,
                title=title,
                category=category,
                description=description,
                image_filename=image_filename,
                address=address,
                area=area,
                landmark=landmark,
                department_id=department.id if department else None,
                priority='Medium',
                status='Submitted',
            )
            db.session.add(complaint)
            db.session.flush()  # get complaint.id before creating history

            # Initial status history entry
            history = ComplaintStatusHistory(
                complaint_id=complaint.id,
                previous_status=None,
                new_status='Submitted',
                updated_by=current_user.id,
                remarks='Complaint submitted by citizen.',
            )
            db.session.add(history)
            db.session.commit()

            flash(f'Complaint submitted successfully! Your Complaint ID is {cid}. Please save it for tracking.', 'success')
            return redirect(url_for('complaints.detail', complaint_id=cid))

        except Exception:
            db.session.rollback()
            flash('An error occurred while submitting your complaint. Please try again.', 'danger')
            return render_template(
                'complaints/submit.html',
                categories=COMPLAINT_CATEGORIES,
            )

    return render_template(
        'complaints/submit.html',
        categories=COMPLAINT_CATEGORIES,
    )


# ═══════════════════════════════════════════════════════════════════════
#  VIEW COMPLAINT DETAIL
# ═══════════════════════════════════════════════════════════════════════

@complaints_bp.route('/<complaint_id>')
@login_required
def detail(complaint_id):
    """View full complaint details (citizen sees own, admin sees all)."""
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first_or_404()

    # Citizens can only view their own complaints
    if current_user.is_citizen and complaint.user_id != current_user.id:
        abort(403)

    # Admin should use admin detail page
    if current_user.is_admin:
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint_id))

    history = complaint.status_history.all()

    return render_template(
        'citizen/complaint_detail.html',
        complaint=complaint,
        history=history,
    )


# ═══════════════════════════════════════════════════════════════════════
#  TRACK COMPLAINT
# ═══════════════════════════════════════════════════════════════════════

@complaints_bp.route('/track')
@login_required
@citizen_required
def track():
    """Track a complaint by its ID."""
    cid = request.args.get('complaint_id', '').strip()
    complaint = None
    searched = bool(cid)

    if cid:
        complaint = Complaint.query.filter_by(
            complaint_id=cid,
            user_id=current_user.id,
        ).first()

    return render_template(
        'citizen/track_complaint.html',
        complaint=complaint,
        searched=searched,
    )


# ═══════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════════════

@complaints_bp.route('/<complaint_id>/feedback', methods=['GET', 'POST'])
@login_required
@citizen_required
def feedback(complaint_id):
    """Submit feedback for a resolved complaint."""
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first_or_404()

    # Ownership check
    if complaint.user_id != current_user.id:
        abort(403)

    # Only allow feedback on resolved complaints
    if complaint.status != 'Resolved':
        flash('Feedback can only be submitted for resolved complaints.', 'warning')
        return redirect(url_for('complaints.detail', complaint_id=complaint_id))

    # Check for existing feedback
    if complaint.feedback:
        flash('You have already submitted feedback for this complaint.', 'info')
        return redirect(url_for('complaints.detail', complaint_id=complaint_id))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '').strip()

        if not rating or rating < 1 or rating > 5:
            flash('Please provide a rating between 1 and 5.', 'danger')
            return render_template('citizen/feedback.html', complaint=complaint)

        try:
            fb = Feedback(
                complaint_id=complaint.id,
                user_id=current_user.id,
                rating=rating,
                comment=comment,
            )
            db.session.add(fb)
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('complaints.detail', complaint_id=complaint_id))
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')

    return render_template('citizen/feedback.html', complaint=complaint)
