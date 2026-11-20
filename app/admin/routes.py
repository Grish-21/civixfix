"""
CivicFix – Admin Blueprint Routes
Handles administrative dashboard, complaint lifecycle management,
department administration, citizen management, analytics & reporting,
and admin profile management.
"""

import calendar
from datetime import datetime, timezone

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    abort,
)
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from app.admin import admin_bp
from app.extensions import db
from app.models import (
    User,
    Department,
    Complaint,
    ComplaintStatusHistory,
    Resolution,
    Feedback,
    ContactMessage,
    COMPLAINT_CATEGORIES,
    COMPLAINT_STATUSES,
    PRIORITY_LEVELS,
    CATEGORY_DEPARTMENT_MAP,
)
from app.utils import (
    admin_required,
    save_uploaded_image,
    allowed_file,
)


# ═══════════════════════════════════════════════════════════════════════
#  1. ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard overview with key statistics and quick metrics."""

    # ── Status counts ─────────────────────────────────────────────────
    total_complaints = Complaint.query.count()
    new_complaints = Complaint.query.filter_by(status='Submitted').count()
    under_review = Complaint.query.filter_by(status='Under Review').count()
    verified = Complaint.query.filter_by(status='Verified').count()
    assigned = Complaint.query.filter_by(status='Assigned').count()
    in_progress = Complaint.query.filter_by(status='In Progress').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    rejected = Complaint.query.filter_by(status='Rejected').count()

    stats = {
        'total': total_complaints,
        'total_complaints': total_complaints,
        'new': new_complaints,
        'submitted': new_complaints,
        'under_review': under_review,
        'verified': verified,
        'assigned': assigned,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
    }

    # ── Recent 5 complaints ───────────────────────────────────────────
    recent_complaints = (
        Complaint.query
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )

    # ── Category statistics (for Chart.js) ────────────────────────────
    cat_counts_query = (
        db.session.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category)
        .all()
    )
    cat_dict = dict(cat_counts_query)
    category_stats = [
        {'category': cat, 'count': cat_dict.get(cat, 0)}
        for cat in COMPLAINT_CATEGORIES
    ]
    # Include any custom/unlisted categories found in the database
    for cat, count in cat_dict.items():
        if cat not in COMPLAINT_CATEGORIES:
            category_stats.append({'category': cat, 'count': count})

    # ── Monthly statistics for current year ───────────────────────────
    current_year = datetime.now(timezone.utc).year
    start_of_year = datetime(current_year, 1, 1)

    complaints_this_year = (
        Complaint.query
        .with_entities(Complaint.created_at)
        .filter(Complaint.created_at >= start_of_year)
        .all()
    )
    month_counts = {m: 0 for m in range(1, 13)}
    for (created_at,) in complaints_this_year:
        if created_at and created_at.year == current_year:
            month_counts[created_at.month] += 1

    monthly_stats = [
        {'month': calendar.month_abbr[m], 'month_num': m, 'count': month_counts[m]}
        for m in range(1, 13)
    ]

    # ── Department statistics ─────────────────────────────────────────
    dept_counts_query = (
        db.session.query(Department.department_name, func.count(Complaint.id))
        .join(Complaint, Complaint.department_id == Department.id, isouter=True)
        .group_by(Department.id, Department.department_name)
        .order_by(Department.department_name)
        .all()
    )
    department_stats = [
        {'department_name': dept_name, 'count': count}
        for dept_name, count in dept_counts_query
    ]
    unassigned_count = Complaint.query.filter(Complaint.department_id.is_(None)).count()
    if unassigned_count > 0:
        department_stats.append({'department_name': 'Unassigned', 'count': unassigned_count})

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        total_complaints=total_complaints,
        new_complaints=new_complaints,
        under_review=under_review,
        verified=verified,
        assigned=assigned,
        in_progress=in_progress,
        resolved=resolved,
        rejected=rejected,
        recent_complaints=recent_complaints,
        category_stats=category_stats,
        monthly_stats=monthly_stats,
        department_stats=department_stats,
        current_year=current_year,
    )


# ═══════════════════════════════════════════════════════════════════════
#  2. ALL COMPLAINTS (SEARCH & FILTER)
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/complaints')
@login_required
@admin_required
def complaints():
    """Paginated list of all complaints with full search and filtering."""

    query = Complaint.query.join(User, Complaint.user_id == User.id)

    # Search filter (by complaint_id, title, description, area, or citizen name)
    search_query = request.args.get('search', '').strip()
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                Complaint.complaint_id.ilike(search_pattern),
                Complaint.title.ilike(search_pattern),
                Complaint.description.ilike(search_pattern),
                Complaint.area.ilike(search_pattern),
                Complaint.landmark.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )

    # Status filter
    status_filter = request.args.get('status', '').strip()
    if status_filter and status_filter in COMPLAINT_STATUSES:
        query = query.filter(Complaint.status == status_filter)

    # Category filter
    category_filter = request.args.get('category', '').strip()
    if category_filter and category_filter in COMPLAINT_CATEGORIES:
        query = query.filter(Complaint.category == category_filter)

    # Priority filter
    priority_filter = request.args.get('priority', '').strip()
    if priority_filter and priority_filter in PRIORITY_LEVELS:
        query = query.filter(Complaint.priority == priority_filter)

    # Department filter
    dept_id_filter = request.args.get('department_id', '').strip()
    if dept_id_filter:
        try:
            dept_id_val = int(dept_id_filter)
            query = query.filter(Complaint.department_id == dept_id_val)
        except ValueError:
            pass

    # Sorting
    sort_order = request.args.get('sort', 'newest').strip()
    if sort_order == 'oldest':
        query = query.order_by(Complaint.created_at.asc())
    else:
        sort_order = 'newest'
        query = query.order_by(Complaint.created_at.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COMPLAINTS_PER_PAGE', 10)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    departments = Department.query.order_by(Department.department_name).all()

    return render_template(
        'admin/complaints.html',
        complaints=pagination,
        pagination=pagination,
        departments=departments,
        categories=COMPLAINT_CATEGORIES,
        COMPLAINT_CATEGORIES=COMPLAINT_CATEGORIES,
        statuses=COMPLAINT_STATUSES,
        COMPLAINT_STATUSES=COMPLAINT_STATUSES,
        priorities=PRIORITY_LEVELS,
        PRIORITY_LEVELS=PRIORITY_LEVELS,
        search=search_query,
        current_status=status_filter,
        current_category=category_filter,
        current_priority=priority_filter,
        current_department=dept_id_filter,
        current_sort=sort_order,
    )


# ═══════════════════════════════════════════════════════════════════════
#  3. COMPLAINT DETAIL VIEW
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/complaints/<string:complaint_id>')
@login_required
@admin_required
def complaint_detail(complaint_id):
    """View complete details for a complaint including history, department,
    resolution and feedback."""

    complaint = Complaint.query.filter(
        or_(
            Complaint.complaint_id == complaint_id,
            Complaint.id == int(complaint_id) if complaint_id.isdigit() else False
        )
    ).first_or_404()

    # Active departments for assignment dropdown
    departments = Department.query.filter_by(is_active=True).order_by(Department.department_name).all()

    # Full audit history ordered chronologically (newest first for display)
    status_history = (
        complaint.status_history
        .order_by(ComplaintStatusHistory.created_at.desc())
        .all()
    )

    return render_template(
        'admin/complaint_detail.html',
        complaint=complaint,
        citizen=complaint.citizen,
        department=complaint.department,
        departments=departments,
        status_history=status_history,
        resolution=complaint.resolution,
        feedback=complaint.feedback,
        COMPLAINT_STATUSES=COMPLAINT_STATUSES,
        PRIORITY_LEVELS=PRIORITY_LEVELS,
    )


# ═══════════════════════════════════════════════════════════════════════
#  4. UPDATE COMPLAINT (STATUS, PRIORITY, DEPARTMENT, REMARKS)
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/complaints/<string:complaint_id>/update', methods=['POST'])
@login_required
@admin_required
def update_complaint(complaint_id):
    """Update status, priority, department, and admin remarks for a complaint."""

    complaint = Complaint.query.filter(
        or_(
            Complaint.complaint_id == complaint_id,
            Complaint.id == int(complaint_id) if complaint_id.isdigit() else False
        )
    ).first_or_404()

    new_status = request.form.get('status', '').strip()
    new_priority = request.form.get('priority', '').strip()
    dept_id_raw = request.form.get('department_id', '').strip()
    admin_remarks = (
        request.form.get('admin_remarks', '').strip()
        or request.form.get('remarks', '').strip()
    )

    # Validation: Resolving must be done via the dedicated resolve route
    if new_status == 'Resolved':
        flash(
            'To resolve a complaint, please use the "Resolve Complaint" section and provide full resolution details.',
            'warning'
        )
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))

    # Department assignment handling
    assigned_dept_id = complaint.department_id
    if dept_id_raw:
        try:
            parsed_dept_id = int(dept_id_raw)
            target_dept = db.session.get(Department, parsed_dept_id)
            if target_dept:
                assigned_dept_id = target_dept.id
            else:
                flash('Selected department does not exist.', 'danger')
                return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))
        except ValueError:
            pass

    # Validation: To mark as 'Assigned', a department must be set
    if new_status == 'Assigned' and not assigned_dept_id:
        flash('Please select a department before changing status to "Assigned".', 'warning')
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))

    try:
        now = datetime.now(timezone.utc)
        complaint.department_id = assigned_dept_id

        # Update priority if valid
        if new_priority in PRIORITY_LEVELS:
            complaint.priority = new_priority

        # Update admin remarks if provided
        if admin_remarks:
            complaint.admin_remarks = admin_remarks

        # Handle status transition if valid and changed
        if new_status and new_status in COMPLAINT_STATUSES and new_status != complaint.status:
            old_status = complaint.status
            complaint.status = new_status

            # Create audit trail
            history_entry = ComplaintStatusHistory(
                complaint_id=complaint.id,
                previous_status=old_status,
                new_status=new_status,
                updated_by=current_user.id,
                remarks=admin_remarks or f'Status updated from {old_status} to {new_status}',
                created_at=now,
            )
            db.session.add(history_entry)

        complaint.updated_at = now
        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} updated successfully.', 'success')

    except Exception:
        db.session.rollback()
        flash('An error occurred while updating the complaint. Please try again.', 'danger')

    return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))


# ═══════════════════════════════════════════════════════════════════════
#  5. RESOLVE COMPLAINT
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/complaints/<string:complaint_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_complaint(complaint_id):
    """Mark a complaint as resolved with detailed explanation and optional proof photo."""

    complaint = Complaint.query.filter(
        or_(
            Complaint.complaint_id == complaint_id,
            Complaint.id == int(complaint_id) if complaint_id.isdigit() else False
        )
    ).first_or_404()

    resolution_description = (
        request.form.get('resolution_description', '').strip()
        or request.form.get('description', '').strip()
    )

    if not resolution_description:
        flash('Resolution description is required.', 'danger')
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))

    # Optional resolution proof image upload
    image_file = request.files.get('resolution_image') or request.files.get('image')
    image_filename = None

    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            flash('Invalid image format. Allowed formats: JPG, JPEG, PNG.', 'danger')
            return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))
        image_filename = save_uploaded_image(image_file, subfolder='resolutions')

    try:
        now = datetime.now(timezone.utc)
        old_status = complaint.status

        # Create or update resolution record
        if complaint.resolution:
            complaint.resolution.resolution_description = resolution_description
            complaint.resolution.admin_id = current_user.id
            complaint.resolution.resolved_at = now
            if image_filename:
                complaint.resolution.resolution_image = image_filename
        else:
            resolution = Resolution(
                complaint_id=complaint.id,
                admin_id=current_user.id,
                resolution_description=resolution_description,
                resolution_image=image_filename,
                resolved_at=now,
            )
            db.session.add(resolution)

        # Update complaint status and resolution timestamp
        complaint.status = 'Resolved'
        complaint.resolved_at = now
        complaint.updated_at = now

        # Update admin remarks if supplied
        extra_remarks = request.form.get('admin_remarks', '').strip()
        if extra_remarks:
            complaint.admin_remarks = extra_remarks

        # Create audit trail
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            previous_status=old_status,
            new_status='Resolved',
            updated_by=current_user.id,
            remarks=resolution_description,
            created_at=now,
        )
        db.session.add(history)

        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} has been marked as Resolved.', 'success')

    except Exception:
        db.session.rollback()
        flash('An error occurred while resolving the complaint. Please try again.', 'danger')

    return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))


# ═══════════════════════════════════════════════════════════════════════
#  6. REJECT COMPLAINT
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/complaints/<string:complaint_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_complaint(complaint_id):
    """Reject a complaint with a mandatory rejection explanation."""

    complaint = Complaint.query.filter(
        or_(
            Complaint.complaint_id == complaint_id,
            Complaint.id == int(complaint_id) if complaint_id.isdigit() else False
        )
    ).first_or_404()

    remarks = (
        request.form.get('remarks', '').strip()
        or request.form.get('rejection_reason', '').strip()
        or request.form.get('admin_remarks', '').strip()
    )

    if not remarks:
        flash('Please provide a reason for rejecting the complaint.', 'danger')
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))

    try:
        now = datetime.now(timezone.utc)
        old_status = complaint.status

        complaint.status = 'Rejected'
        complaint.admin_remarks = remarks
        complaint.updated_at = now

        # Create audit trail
        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            previous_status=old_status,
            new_status='Rejected',
            updated_by=current_user.id,
            remarks=remarks,
            created_at=now,
        )
        db.session.add(history)

        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} has been marked as Rejected.', 'warning')

    except Exception:
        db.session.rollback()
        flash('An error occurred while rejecting the complaint. Please try again.', 'danger')

    return redirect(url_for('admin.complaint_detail', complaint_id=complaint.complaint_id))


# ═══════════════════════════════════════════════════════════════════════
#  7. DEPARTMENTS LIST
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    """List all municipal departments with associated complaint counts."""

    dept_records = Department.query.order_by(Department.department_name).all()

    # Batch query complaint counts per department
    counts_map = dict(
        db.session.query(Complaint.department_id, func.count(Complaint.id))
        .filter(Complaint.department_id.isnot(None))
        .group_by(Complaint.department_id)
        .all()
    )

    for dept in dept_records:
        dept.complaint_count = counts_map.get(dept.id, 0)

    return render_template(
        'admin/departments.html',
        departments=dept_records,
    )


# ═══════════════════════════════════════════════════════════════════════
#  8. ADD DEPARTMENT
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    """Add a new municipal department."""

    department_name = request.form.get('department_name', '').strip()
    description = request.form.get('description', '').strip()

    if not department_name:
        flash('Department name is required.', 'danger')
        return redirect(url_for('admin.departments'))

    # Check uniqueness (case-insensitive)
    existing = Department.query.filter(
        func.lower(Department.department_name) == func.lower(department_name)
    ).first()

    if existing:
        flash(f'A department named "{department_name}" already exists.', 'warning')
        return redirect(url_for('admin.departments'))

    try:
        new_dept = Department(
            department_name=department_name,
            description=description,
            is_active=True,
        )
        db.session.add(new_dept)
        db.session.commit()
        flash(f'Department "{department_name}" added successfully.', 'success')

    except Exception:
        db.session.rollback()
        flash('An error occurred while creating the department. Please try again.', 'danger')

    return redirect(url_for('admin.departments'))


# ═══════════════════════════════════════════════════════════════════════
#  9. UPDATE DEPARTMENT
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/departments/<int:dept_id>/update', methods=['POST'])
@login_required
@admin_required
def update_department(dept_id):
    """Update department name, description, and active status."""

    dept = Department.query.get_or_404(dept_id)

    department_name = request.form.get('department_name', '').strip()
    description = request.form.get('description', '').strip()

    if not department_name:
        flash('Department name cannot be empty.', 'danger')
        return redirect(url_for('admin.departments'))

    # Check name collision with another department
    existing = Department.query.filter(
        func.lower(Department.department_name) == func.lower(department_name),
        Department.id != dept.id
    ).first()

    if existing:
        flash(f'Another department named "{department_name}" already exists.', 'warning')
        return redirect(url_for('admin.departments'))

    try:
        dept.department_name = department_name
        dept.description = description

        # Update is_active if explicitly passed
        if 'is_active' in request.form:
            dept.is_active = request.form.get('is_active') in ['1', 'true', 'True', 'on', True]

        db.session.commit()
        flash(f'Department "{dept.department_name}" updated successfully.', 'success')

    except Exception:
        db.session.rollback()
        flash('An error occurred while updating the department. Please try again.', 'danger')

    return redirect(url_for('admin.departments'))


# ═══════════════════════════════════════════════════════════════════════
#  10. TOGGLE DEPARTMENT STATUS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/departments/<int:dept_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_department(dept_id):
    """Toggle a department active / inactive state."""

    dept = Department.query.get_or_404(dept_id)

    try:
        dept.is_active = not dept.is_active
        db.session.commit()
        status_label = 'activated' if dept.is_active else 'deactivated'
        flash(f'Department "{dept.department_name}" has been {status_label}.', 'info')

    except Exception:
        db.session.rollback()
        flash('An error occurred while toggling department status.', 'danger')

    return redirect(url_for('admin.departments'))


# ═══════════════════════════════════════════════════════════════════════
#  11. CITIZENS LIST
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/citizens')
@login_required
@admin_required
def citizens():
    """List all registered citizen users with pagination and their complaint counts."""

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COMPLAINTS_PER_PAGE', 10)
    search_query = request.args.get('search', '').strip()

    query = User.query.filter_by(role='citizen')

    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.mobile.ilike(search_pattern),
                User.address.ilike(search_pattern),
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Attach complaint count to each citizen in current page
    citizen_ids = [c.id for c in pagination.items]
    if citizen_ids:
        counts = dict(
            db.session.query(Complaint.user_id, func.count(Complaint.id))
            .filter(Complaint.user_id.in_(citizen_ids))
            .group_by(Complaint.user_id)
            .all()
        )
        for citizen in pagination.items:
            citizen.complaint_count = counts.get(citizen.id, 0)
    else:
        for citizen in pagination.items:
            citizen.complaint_count = 0

    return render_template(
        'admin/citizens.html',
        citizens=pagination,
        pagination=pagination,
        search=search_query,
    )


# ═══════════════════════════════════════════════════════════════════════
#  12. REPORTS & ANALYTICS
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Comprehensive analytical reports and charts for municipal performance."""

    # 1. Complaints by Category
    cat_counts = (
        db.session.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    complaints_by_category = [
        {'category': cat, 'count': count}
        for cat, count in cat_counts
    ]

    # 2. Complaints by Department
    dept_counts = (
        db.session.query(Department.department_name, func.count(Complaint.id))
        .join(Complaint, Complaint.department_id == Department.id, isouter=True)
        .group_by(Department.id, Department.department_name)
        .order_by(func.count(Complaint.id).desc())
        .all()
    )
    complaints_by_department = [
        {'department_name': dept_name, 'count': count}
        for dept_name, count in dept_counts
    ]
    unassigned_count = Complaint.query.filter(Complaint.department_id.is_(None)).count()
    if unassigned_count > 0:
        complaints_by_department.append({'department_name': 'Unassigned', 'count': unassigned_count})

    # 3. Complaints by Status
    status_counts_map = dict(
        db.session.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .all()
    )
    complaints_by_status = [
        {'status': s, 'count': status_counts_map.get(s, 0)}
        for s in COMPLAINT_STATUSES
    ]

    # 4. Top 10 Areas by Complaints
    area_counts = (
        db.session.query(Complaint.area, func.count(Complaint.id))
        .filter(Complaint.area.isnot(None), Complaint.area != '')
        .group_by(Complaint.area)
        .order_by(func.count(Complaint.id).desc())
        .limit(10)
        .all()
    )
    complaints_by_area = [
        {'area': area, 'count': count}
        for area, count in area_counts
    ]

    # 5. Monthly Trends (current year)
    current_year = datetime.now(timezone.utc).year
    start_of_year = datetime(current_year, 1, 1)

    complaints_this_year = (
        Complaint.query
        .with_entities(Complaint.created_at)
        .filter(Complaint.created_at >= start_of_year)
        .all()
    )
    month_counts = {m: 0 for m in range(1, 13)}
    for (created_at,) in complaints_this_year:
        if created_at and created_at.year == current_year:
            month_counts[created_at.month] += 1

    monthly_trends = [
        {'month': calendar.month_abbr[m], 'month_num': m, 'count': month_counts[m]}
        for m in range(1, 13)
    ]

    # 6. Resolved vs Unresolved
    resolved_count = Complaint.query.filter_by(status='Resolved').count()
    total_count = Complaint.query.count()
    unresolved_count = max(0, total_count - resolved_count)
    resolved_vs_unresolved = {
        'resolved': resolved_count,
        'unresolved': unresolved_count,
    }

    # 7. Average Resolution Time (in days)
    resolved_complaints = (
        Complaint.query
        .filter(Complaint.status == 'Resolved', Complaint.resolved_at.isnot(None))
        .with_entities(Complaint.created_at, Complaint.resolved_at)
        .all()
    )

    if resolved_complaints:
        total_days = sum(
            max(0.0, (resolved_at - created_at).total_seconds() / 86400.0)
            for created_at, resolved_at in resolved_complaints
            if created_at and resolved_at
        )
        avg_resolution_time = round(total_days / len(resolved_complaints), 1)
    else:
        avg_resolution_time = 0.0

    return render_template(
        'admin/reports.html',
        complaints_by_category=complaints_by_category,
        complaints_by_department=complaints_by_department,
        complaints_by_status=complaints_by_status,
        complaints_by_area=complaints_by_area,
        monthly_trends=monthly_trends,
        resolved_vs_unresolved=resolved_vs_unresolved,
        avg_resolution_time=avg_resolution_time,
        current_year=current_year,
        total_complaints=total_count,
    )


# ═══════════════════════════════════════════════════════════════════════
#  13. ADMIN PROFILE VIEW
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/profile')
@login_required
@admin_required
def profile():
    """View admin user profile details."""
    return render_template('admin/profile.html', user=current_user, admin=current_user)


# ═══════════════════════════════════════════════════════════════════════
#  14. UPDATE ADMIN PROFILE
# ═══════════════════════════════════════════════════════════════════════

@admin_bp.route('/profile/update', methods=['POST'])
@login_required
@admin_required
def update_profile():
    """Update admin contact details and address."""

    full_name = request.form.get('full_name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    address = request.form.get('address', '').strip()

    errors = []
    if not full_name or len(full_name) < 2:
        errors.append('Full name must be at least 2 characters.')
    if not mobile or len(mobile) < 7:
        errors.append('Please provide a valid contact number.')
    if not address or len(address) < 3:
        errors.append('Address must be at least 3 characters.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('admin.profile'))

    try:
        current_user.full_name = full_name
        current_user.mobile = mobile
        current_user.address = address
        current_user.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')

    except Exception:
        db.session.rollback()
        flash('An error occurred while updating your profile. Please try again.', 'danger')

    return redirect(url_for('admin.profile'))
