import pytest
import sys
import os

from app.forms import (
    RegistrationForm, LoginForm, BoardForm, 
    ColumnForm, CardForm, SettingsForm, ShareBoardForm
)
from app.models import User


def test_registration_form_validation(app):
    """Test registration form validation."""
    with app.app_context():
        # Create a test user for duplicate validation
        from app import db
        user = User(username='existinguser', email='existing@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Test valid form
        form = RegistrationForm(
            username='newuser',
            email='new@example.com',
            password='password',
            confirm_password='password'
        )
        assert form.validate() is True
        
        # Test username too short
        form = RegistrationForm(
            username='a',  # Too short
            email='new@example.com',
            password='password',
            confirm_password='password'
        )
        assert form.validate() is False
        assert 'Field must be between 2 and 20 characters long.' in form.username.errors
        
        # Test username too long
        form = RegistrationForm(
            username='a' * 21,  # Too long
            email='new@example.com',
            password='password',
            confirm_password='password'
        )
        assert form.validate() is False
        assert 'Field must be between 2 and 20 characters long.' in form.username.errors
        
        # Test invalid email
        form = RegistrationForm(
            username='newuser',
            email='not-an-email',  # Invalid email
            password='password',
            confirm_password='password'
        )
        assert form.validate() is False
        assert 'Invalid email address.' in form.email.errors
        
        # Test password mismatch
        form = RegistrationForm(
            username='newuser',
            email='new@example.com',
            password='password',
            confirm_password='different'  # Doesn't match
        )
        assert form.validate() is False
        assert 'Field must be equal to password.' in form.confirm_password.errors
        
        # Test duplicate username
        form = RegistrationForm(
            username='existinguser',  # Already exists
            email='new@example.com',
            password='password',
            confirm_password='password'
        )
        assert form.validate() is False
        assert 'That username is already taken. Please choose a different one.' in form.username.errors
        
        # Test duplicate email
        form = RegistrationForm(
            username='newuser',
            email='existing@example.com',  # Already exists
            password='password',
            confirm_password='password'
        )
        assert form.validate() is False
        assert 'That email is already registered. Please use a different one.' in form.email.errors


def test_login_form_validation(app):
    """Test login form validation."""
    with app.app_context():
        # Test valid form
        form = LoginForm(
            email='test@example.com',
            password='password'
        )
        assert form.validate() is True
        
        # Test missing email
        form = LoginForm(
            email='',
            password='password'
        )
        assert form.validate() is False
        assert 'This field is required.' in form.email.errors
        
        # Test invalid email
        form = LoginForm(
            email='not-an-email',
            password='password'
        )
        assert form.validate() is False
        assert 'Invalid email address.' in form.email.errors
        
        # Test missing password
        form = LoginForm(
            email='test@example.com',
            password=''
        )
        assert form.validate() is False
        assert 'This field is required.' in form.password.errors


def test_board_form_validation(app):
    """Test board form validation."""
    with app.app_context():
        # Test valid form
        form = BoardForm(
            title='Test Board'
        )
        assert form.validate() is True
        
        # Test missing title
        form = BoardForm(
            title=''
        )
        assert form.validate() is False
        assert 'This field is required.' in form.title.errors
        
        # Test title too long
        form = BoardForm(
            title='a' * 101  # Too long
        )
        assert form.validate() is False
        assert 'Field cannot be longer than 100 characters.' in form.title.errors


def test_column_form_validation(app):
    """Test column form validation."""
    with app.app_context():
        # Test valid form
        form = ColumnForm(
            title='Test Column'
        )
        assert form.validate() is True
        
        # Test missing title
        form = ColumnForm(
            title=''
        )
        assert form.validate() is False
        assert 'This field is required.' in form.title.errors
        
        # Test title too long
        form = ColumnForm(
            title='a' * 101  # Too long
        )
        assert form.validate() is False
        assert 'Field cannot be longer than 100 characters.' in form.title.errors


def test_card_form_validation(app):
    """Test card form validation."""
    with app.app_context():
        # Test valid form
        form = CardForm(
            title='Test Card',
            description='Test Description'
        )
        assert form.validate() is True
        
        # Test missing title
        form = CardForm(
            title='',
            description='Test Description'
        )
        assert form.validate() is False
        assert 'This field is required.' in form.title.errors
        
        # Test title too long
        form = CardForm(
            title='a' * 101,  # Too long
            description='Test Description'
        )
        assert form.validate() is False
        assert 'Field cannot be longer than 100 characters.' in form.title.errors


def test_settings_form_validation(app):
    """Test settings form validation."""
    with app.app_context():
        # Test with dark mode on
        form = SettingsForm(
            dark_mode=True
        )
        assert form.validate() is True
        
        # Test with dark mode off
        form = SettingsForm(
            dark_mode=False
        )
        assert form.validate() is True


def test_share_board_form_validation(app, init_database):
    """Test share board form validation."""
    with app.app_context():
        # Test valid form with view permission
        form = ShareBoardForm(
            user_email='other@example.com',
            permission='view'
        )
        assert form.validate() is True
        
        # Test valid form with edit permission
        form = ShareBoardForm(
            user_email='other@example.com',
            permission='edit'
        )
        assert form.validate() is True
        
        # Test invalid email
        form = ShareBoardForm(
            user_email='not-an-email',
            permission='view'
        )
        assert form.validate() is False
        assert 'Invalid email address.' in form.user_email.errors
        
        # Test non-existent user
        form = ShareBoardForm(
            user_email='nonexistent@example.com',
            permission='view'
        )
        assert form.validate() is False
        assert 'No user found with this email address.' in form.user_email.errors
        
        # Test invalid permission
        form = ShareBoardForm(
            user_email='other@example.com',
            permission='invalid'  # Not a valid choice
        )
        assert form.validate() is False
        assert 'Not a valid choice.' in form.permission.errors
