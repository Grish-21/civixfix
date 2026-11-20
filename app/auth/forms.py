"""
CivicFix – Auth WTForms
Login and Registration forms with server-side validation.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Regexp, ValidationError,
)
from app.models import User


class LoginForm(FlaskForm):
    """Login form for citizens and admins."""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
    ])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """Registration form for new citizen accounts."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=150, message='Name must be between 2 and 150 characters.'),
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=150),
    ])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(message='Mobile number is required.'),
        Regexp(r'^\d{10}$', message='Please enter a valid 10-digit mobile number.'),
    ])
    address = StringField('Address / Area', validators=[
        DataRequired(message='Address is required.'),
        Length(min=5, max=300, message='Address must be between 5 and 300 characters.'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=6, max=128, message='Password must be at least 6 characters.'),
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords do not match.'),
    ])
    submit = SubmitField('Create Account')

    # ── Custom validators ─────────────────────────────────────────────

    def validate_email(self, field):
        """Reject duplicate email addresses."""
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('An account with this email already exists.')
