"""
CivicFix – Automated System & Workflow Verification Suite
Validates registration, authentication, RBAC, complaint lifecycle,
department operations, resolutions, feedback, and analytics.
"""

import os
import unittest
from app import create_app
from app.extensions import db
from app.models import (
    User, Department, Complaint, ComplaintStatusHistory,
    Resolution, Feedback, ContactMessage
)


class CivicFixTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing with in-memory SQLite
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,  # Disable CSRF for programmatic tests
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Re-create database in memory & seed
        db.drop_all()
        db.create_all()
        from app.seed import seed_database
        seed_database()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ── 1. AUTHENTICATION & REGISTRATION TESTS ──────────────────────

    def test_demo_accounts_seeded(self):
        """Verify citizen and admin demo accounts exist with correct roles."""
        citizen = User.query.filter_by(email='citizen@civicfix.demo').first()
        self.assertIsNotNone(citizen)
        self.assertTrue(citizen.is_citizen)
        self.assertTrue(citizen.check_password('Citizen@123'))

        admin = User.query.filter_by(email='admin@civicfix.demo').first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.check_password('Admin@123'))

    def test_citizen_registration(self):
        """Test valid citizen registration."""
        res = self.client.post('/auth/register', data={
            'full_name': 'Test Citizen',
            'email': 'testuser@example.com',
            'mobile': '9876543210',
            'address': 'Flat 101, Green Heights',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        user = User.query.filter_by(email='testuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.full_name, 'Test Citizen')
        self.assertEqual(user.role, 'citizen')
        self.assertTrue(user.check_password('Password@123'))

    def test_registration_duplicate_email(self):
        """Prevent duplicate email registrations."""
        res = self.client.post('/auth/register', data={
            'full_name': 'Duplicate User',
            'email': 'citizen@civicfix.demo',
            'mobile': '9876543210',
            'address': 'Some Address',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
        }, follow_redirects=True)
        self.assertIn(b'An account with this email already exists', res.data)

    def test_registration_password_mismatch(self):
        """Reject mismatched passwords."""
        res = self.client.post('/auth/register', data={
            'full_name': 'Mismatch User',
            'email': 'mismatch@example.com',
            'mobile': '9876543210',
            'address': 'Some Address',
            'password': 'Password@123',
            'confirm_password': 'Password@456',
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', res.data)

    def test_login_and_logout(self):
        """Test login redirect and logout."""
        # Citizen login
        res = self.client.post('/auth/login', data={
            'email': 'citizen@civicfix.demo',
            'password': 'Citizen@123',
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dashboard', res.data)

        # Logout
        res_logout = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b'You have been logged out', res_logout.data)

    def test_admin_rbac_protection(self):
        """Citizens cannot access admin portal."""
        # Log in as citizen
        self.client.post('/auth/login', data={
            'email': 'citizen@civicfix.demo',
            'password': 'Citizen@123',
        })
        # Try accessing admin dashboard
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 403)

    # ── 2. COMPLAINT WORKFLOW TESTS ─────────────────────────────────

    def test_complaint_lifecycle(self):
        """Complete lifecycle: submit -> verify -> assign -> in progress -> resolve -> feedback."""
        # 1. Citizen logs in and submits complaint
        self.client.post('/auth/login', data={
            'email': 'citizen@civicfix.demo',
            'password': 'Citizen@123',
        })
        res = self.client.post('/complaints/submit', data={
            'title': 'Pothole on Main Street',
            'category': 'Road Damage / Potholes',
            'description': 'Deep pothole causing vehicle damage near city library.',
            'address': 'Near City Central Library',
            'area': 'Civic Zone A',
            'landmark': 'Library Gate 2',
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check DB for complaint
        complaint = Complaint.query.first()
        self.assertIsNotNone(complaint)
        self.assertTrue(complaint.complaint_id.startswith('CF-'))
        self.assertEqual(complaint.status, 'Submitted')
        self.assertEqual(complaint.category, 'Road Damage / Potholes')
        # Check automatic department mapping to Road Department
        self.assertEqual(complaint.department.department_name, 'Road Department')

        # Check initial audit history entry
        history_entries = complaint.status_history.all()
        self.assertEqual(len(history_entries), 1)
        self.assertEqual(history_entries[0].new_status, 'Submitted')

        cid = complaint.complaint_id

        # 2. Citizen can track their complaint
        track_res = self.client.get(f'/complaints/track?complaint_id={cid}')
        self.assertEqual(track_res.status_code, 200)
        self.assertIn(b'Pothole on Main Street', track_res.data)

        # 3. Another citizen cannot see or track this complaint
        self.client.get('/auth/logout')
        self.client.post('/auth/register', data={
            'full_name': 'Another Citizen',
            'email': 'other@civicfix.demo',
            'mobile': '9876543299',
            'address': 'Other Street',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
        })
        self.client.post('/auth/login', data={
            'email': 'other@civicfix.demo',
            'password': 'Password@123',
        })
        other_detail = self.client.get(f'/complaints/{cid}')
        self.assertEqual(other_detail.status_code, 403)  # Ownership protected

        # 4. Admin logs in and manages complaint
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={
            'email': 'admin@civicfix.demo',
            'password': 'Admin@123',
        })

        # Admin updates status to Under Review
        self.client.post(f'/admin/complaints/{cid}/update', data={
            'status': 'Under Review',
            'priority': 'High',
            'department_id': complaint.department_id,
            'admin_remarks': 'Under administrative review by Road engineer.',
        }, follow_redirects=True)
        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Under Review')
        self.assertEqual(complaint.priority, 'High')

        # Admin advances to In Progress
        self.client.post(f'/admin/complaints/{cid}/update', data={
            'status': 'In Progress',
            'priority': 'High',
            'department_id': complaint.department_id,
            'admin_remarks': 'Patching team deployed to site.',
        }, follow_redirects=True)
        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'In Progress')

        # Admin resolves complaint
        res_resolve = self.client.post(f'/admin/complaints/{cid}/resolve', data={
            'resolution_description': 'Pothole filled with bitumen and road leveled successfully.',
        }, follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)
        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertIsNotNone(complaint.resolution)
        self.assertIn('bitumen', complaint.resolution.resolution_description)

        # 5. Citizen submits feedback
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={
            'email': 'citizen@civicfix.demo',
            'password': 'Citizen@123',
        })
        fb_res = self.client.post(f'/complaints/{cid}/feedback', data={
            'rating': 5,
            'comment': 'Prompt and excellent resolution!',
        }, follow_redirects=True)
        self.assertEqual(fb_res.status_code, 200)
        db.session.refresh(complaint)
        self.assertIsNotNone(complaint.feedback)
        self.assertEqual(complaint.feedback.rating, 5)

        # 6. Duplicate feedback is rejected
        dup_fb = self.client.post(f'/complaints/{cid}/feedback', data={
            'rating': 4,
            'comment': 'Duplicate feedback',
        }, follow_redirects=True)
        self.assertIn(b'already submitted feedback', dup_fb.data)

    def test_rejection_workflow(self):
        """Admin rejects invalid complaint with logged reason."""
        # Submit complaint
        self.client.post('/auth/login', data={
            'email': 'citizen@civicfix.demo',
            'password': 'Citizen@123',
        })
        self.client.post('/complaints/submit', data={
            'title': 'Private garden hedge',
            'category': 'Fallen Trees',
            'description': 'Private hedge overgrowing in backyard.',
            'address': 'Private property 12',
            'area': 'Ward 5',
        })
        complaint = Complaint.query.first()
        cid = complaint.complaint_id

        # Admin rejects
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={
            'email': 'admin@civicfix.demo',
            'password': 'Admin@123',
        })
        res = self.client.post(f'/admin/complaints/{cid}/reject', data={
            'remarks': 'Complaint pertains to private property beyond municipal jurisdiction.',
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Rejected')
        self.assertIn('private property', complaint.admin_remarks)

    # ── 3. DEPARTMENT MANAGEMENT TESTS ──────────────────────────────

    def test_department_crud(self):
        """Admin can add, update, and toggle departments."""
        self.client.post('/auth/login', data={
            'email': 'admin@civicfix.demo',
            'password': 'Admin@123',
        })
        # Add new department
        self.client.post('/admin/departments/add', data={
            'department_name': 'Urban Forestry',
            'description': 'Afforestation and tree preservation unit.',
        }, follow_redirects=True)
        dept = Department.query.filter_by(department_name='Urban Forestry').first()
        self.assertIsNotNone(dept)
        self.assertTrue(dept.is_active)

        # Toggle inactive
        self.client.post(f'/admin/departments/{dept.id}/toggle', follow_redirects=True)
        db.session.refresh(dept)
        self.assertFalse(dept.is_active)

    # ── 4. CONTACT MESSAGE STORAGE ──────────────────────────────────

    def test_contact_form_saves_to_database(self):
        """Contact form saves message to DB without mock email."""
        res = self.client.post('/contact', data={
            'name': 'Inquirer User',
            'email': 'inquiry@civic.org',
            'subject': 'Service Inquiry',
            'message': 'When does garbage collection occur in Ward 3?',
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        msg = ContactMessage.query.filter_by(email='inquiry@civic.org').first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.subject, 'Service Inquiry')


if __name__ == '__main__':
    unittest.main()
