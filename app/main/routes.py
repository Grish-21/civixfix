"""
CivicFix – Main (Public) Routes
Homepage, about, contact, and how-it-works pages.
"""

from flask import render_template, redirect, url_for, flash, request
from app.main import main_bp
from app.extensions import db
from app.models import ContactMessage


@main_bp.route('/')
def index():
    """Public homepage."""
    return render_template('index.html')


@main_bp.route('/about')
def about():
    """About CivicFix page."""
    return render_template('about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form – saves messages to the database."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Server-side validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        if not subject:
            errors.append('Subject is required.')
        if not message:
            errors.append('Message is required.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('contact.html')

        try:
            msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
            )
            db.session.add(msg)
            db.session.commit()
            flash('Your message has been received. We will get back to you soon.', 'success')
            return redirect(url_for('main.contact'))
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')

    return render_template('contact.html')


@main_bp.route('/how-it-works')
def how_it_works():
    """How CivicFix Works page."""
    return render_template('how_it_works.html')
