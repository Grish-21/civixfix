"""
CivicFix – Database Models
All SQLAlchemy ORM models for the application.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


# ═══════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    """Citizen or Admin user account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='citizen')  # 'citizen' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    complaints = db.relationship('Complaint', backref='citizen', lazy='dynamic',
                                 foreign_keys='Complaint.user_id')
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    resolutions = db.relationship('Resolution', backref='admin', lazy='dynamic')

    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_citizen(self):
        return self.role == 'citizen'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# ═══════════════════════════════════════════════════════════════════════
#  DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════════

class Department(db.Model):
    """Municipal department that handles specific complaint categories."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    complaints = db.relationship('Complaint', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.department_name}>'


# ═══════════════════════════════════════════════════════════════════════
#  COMPLAINTS
# ═══════════════════════════════════════════════════════════════════════

# Valid status values (ordered by workflow progression)
COMPLAINT_STATUSES = [
    'Submitted',
    'Under Review',
    'Verified',
    'Assigned',
    'In Progress',
    'Resolved',
    'Rejected',
]

COMPLAINT_CATEGORIES = [
    'Garbage Collection',
    'Road Damage / Potholes',
    'Streetlight Problems',
    'Water Leakage / Water Supply',
    'Drainage Problems',
    'Waterlogging',
    'Traffic Signal Problems',
    'Public Infrastructure',
    'Fallen Trees',
    'Public Toilet Issues',
    'Other Municipal Issues',
]

PRIORITY_LEVELS = ['Low', 'Medium', 'High', 'Urgent']

# Mapping from category to department name (used during seeding & auto-assignment)
CATEGORY_DEPARTMENT_MAP = {
    'Garbage Collection': 'Waste Management',
    'Road Damage / Potholes': 'Road Department',
    'Streetlight Problems': 'Electrical Department',
    'Water Leakage / Water Supply': 'Water Department',
    'Drainage Problems': 'Drainage Department',
    'Waterlogging': 'Drainage Department',
    'Traffic Signal Problems': 'Traffic Department',
    'Public Infrastructure': 'Public Works Department',
    'Fallen Trees': 'Garden / Tree Department',
    'Public Toilet Issues': 'Sanitation Department',
    'Other Municipal Issues': 'General Administration',
}


class Complaint(db.Model):
    """A civic complaint submitted by a citizen."""
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), default=None)
    address = db.Column(db.String(300), nullable=False)
    area = db.Column(db.String(150), nullable=False)
    landmark = db.Column(db.String(200), default='')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True, index=True)
    priority = db.Column(db.String(10), default='Medium', index=True)
    status = db.Column(db.String(20), default='Submitted', nullable=False, index=True)
    admin_remarks = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    status_history = db.relationship('ComplaintStatusHistory', backref='complaint',
                                     lazy='dynamic', order_by='ComplaintStatusHistory.created_at')
    resolution = db.relationship('Resolution', backref='complaint', uselist=False)
    feedback = db.relationship('Feedback', backref='complaint', uselist=False)

    def __repr__(self):
        return f'<Complaint {self.complaint_id} – {self.status}>'


# ═══════════════════════════════════════════════════════════════════════
#  COMPLAINT STATUS HISTORY
# ═══════════════════════════════════════════════════════════════════════

class ComplaintStatusHistory(db.Model):
    """Audit trail for every status change on a complaint."""
    __tablename__ = 'complaint_status_history'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, index=True)
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    remarks = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to the user who made the update
    updater = db.relationship('User', foreign_keys=[updated_by])

    def __repr__(self):
        return f'<StatusHistory {self.previous_status} → {self.new_status}>'


# ═══════════════════════════════════════════════════════════════════════
#  RESOLUTIONS
# ═══════════════════════════════════════════════════════════════════════

class Resolution(db.Model):
    """Resolution details provided by an admin when a complaint is resolved."""
    __tablename__ = 'resolutions'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False,
                             unique=True, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resolution_description = db.Column(db.Text, nullable=False)
    resolution_image = db.Column(db.String(255), default=None)
    resolved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Resolution for Complaint #{self.complaint_id}>'


# ═══════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════════════

class Feedback(db.Model):
    """Citizen feedback on a resolved complaint."""
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False,
                             unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Feedback {self.rating}★ for Complaint #{self.complaint_id}>'


# ═══════════════════════════════════════════════════════════════════════
#  CONTACT MESSAGES
# ═══════════════════════════════════════════════════════════════════════

class ContactMessage(db.Model):
    """Messages submitted through the public contact form."""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ContactMessage from {self.email}>'
