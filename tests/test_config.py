import pytest
import os
import sys

from app import create_app
from config import Config


def test_default_config():
    """Test the default configuration."""
    app = create_app()
    
    # Check default config values
    assert app.config['SECRET_KEY'] == os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
    assert app.config['SQLALCHEMY_DATABASE_URI'] == os.environ.get('DATABASE_URL', 'sqlite:///kanban.db')
    assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False


def test_testing_config():
    """Test the testing configuration."""
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        WTF_CSRF_ENABLED = False
    
    app = create_app(TestConfig)
    
    # Check testing config values
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app.config['WTF_CSRF_ENABLED'] is False


def test_env_config():
    """Test configuration from environment variables."""
    # Create a custom Config class that directly sets the values
    class EnvConfig(Config):
        SECRET_KEY = 'test-secret-key'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    
    # Create app with the custom config
    app = create_app(EnvConfig)
    
    # Check that the custom config values are used
    assert app.config['SECRET_KEY'] == 'test-secret-key'
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///test.db'


def test_blueprints_registered():
    """Test that all blueprints are registered."""
    app = create_app()
    
    # Check that all blueprints are registered
    assert 'main' in app.blueprints
    assert 'auth' in app.blueprints
    assert 'kanban' in app.blueprints
    
    # Check blueprint URLs
    assert app.url_map.bind('localhost').match('/') == ('main.home', {})
    assert app.url_map.bind('localhost').match('/login') == ('auth.login', {})
    assert app.url_map.bind('localhost').match('/boards') == ('kanban.boards', {})
