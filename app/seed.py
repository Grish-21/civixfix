"""
CivicFix – Database Seeder
Creates demo accounts and default departments when the database is first initialised.
Run automatically from the app factory; safe to call repeatedly (idempotent).
"""

from app.extensions import db
from app.models import User, Department, CATEGORY_DEPARTMENT_MAP


def seed_database():
    """Seed demo users and departments if they do not already exist."""

    _seed_departments()
    _seed_demo_users()
    db.session.commit()


# ── Departments ───────────────────────────────────────────────────────

def _seed_departments():
    """Create one Department row for every unique department name in the
    category → department mapping."""

    # Collect unique department names (preserving order)
    seen = set()
    department_names = []
    for dept_name in CATEGORY_DEPARTMENT_MAP.values():
        if dept_name not in seen:
            seen.add(dept_name)
            department_names.append(dept_name)

    for name in department_names:
        if not Department.query.filter_by(department_name=name).first():
            dept = Department(
                department_name=name,
                description=f'Handles complaints related to {name.lower()}.',
                is_active=True,
            )
            db.session.add(dept)


# ── Demo accounts ────────────────────────────────────────────────────

def _seed_demo_users():
    """Create citizen and admin demo accounts if they do not exist."""

    # Demo Citizen
    if not User.query.filter_by(email='citizen@civicfix.demo').first():
        citizen = User(
            full_name='Demo Citizen',
            email='citizen@civicfix.demo',
            mobile='9876543210',
            address='123 Demo Street, Sample Area',
            role='citizen',
            is_active=True,
        )
        citizen.set_password('Citizen@123')
        db.session.add(citizen)

    # Demo Admin
    if not User.query.filter_by(email='admin@civicfix.demo').first():
        admin = User(
            full_name='Demo Admin',
            email='admin@civicfix.demo',
            mobile='9876543211',
            address='Municipal Office, Civic Centre',
            role='admin',
            is_active=True,
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
