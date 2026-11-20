"""
CivicFix – Auth Routes
Handles user registration, login, and logout.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.extensions import db
from app.models import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a citizen or admin user."""
    # Already logged in? Redirect to appropriate dashboard.
    if current_user.is_authenticated:
        return _redirect_by_role()

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Respect ?next= parameter if present
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return _redirect_by_role()
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new citizen account."""
    if current_user.is_authenticated:
        return _redirect_by_role()

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            mobile=form.mobile.data.strip(),
            address=form.address.data.strip(),
            role='citizen',  # Normal registration always creates citizens
            is_active=True,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ── Helpers ───────────────────────────────────────────────────────────

def _redirect_by_role():
    """Redirect to the correct dashboard based on the user's role."""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('citizen.dashboard'))
