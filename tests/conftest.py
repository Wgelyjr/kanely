import os
import pytest
import tempfile
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import create_app, db
from app.models import User, Board, Column, Card, board_shares
from config import Config


class TestConfig(Config):
    """Test configuration that uses a temporary SQLite database."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)
    
    # Create the database and tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def init_database(app):
    """Initialize the database with test data."""
    with app.app_context():
        # Create test users
        user1 = User(username='testuser', email='test@example.com')
        user1.set_password('password')
        user2 = User(username='otheruser', email='other@example.com')
        user2.set_password('password')
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Create a board for user1
        board = Board(title='Test Board', user_id=user1.id)
        db.session.add(board)
        db.session.commit()
        
        # Create columns for the board
        columns = [
            Column(title='To Do', position=0, board_id=board.id),
            Column(title='In Progress', position=1, board_id=board.id),
            Column(title='Done', position=2, board_id=board.id)
        ]
        db.session.add_all(columns)
        db.session.commit()
        
        # Create cards for the first column
        cards = [
            Card(title='Test Card 1', description='Description 1', position=0, column_id=columns[0].id),
            Card(title='Test Card 2', description='Description 2', position=1, column_id=columns[0].id)
        ]
        db.session.add_all(cards)
        db.session.commit()
        
        # Share the board with user2 (view only)
        stmt = board_shares.insert().values(
            user_id=user2.id,
            board_id=board.id,
            can_edit=False
        )
        db.session.execute(stmt)
        db.session.commit()
        
        yield db


@pytest.fixture
def auth_client(client, app, init_database):
    """A test client with authentication."""
    with app.app_context():
        from flask_login import login_user
        from app.models import User
        
        # Find the test user
        user = User.query.filter_by(email='test@example.com').first()
        
        # Make sure the user exists
        assert user is not None, "Test user not found in database"
        
        # Create a test client with the user logged in
        with client.session_transaction() as session:
            # Log in the user
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # Check that the login was successful
            assert b'Login unsuccessful' not in response.data
        
        return client


@pytest.fixture
def other_auth_client(client, app, init_database):
    """A test client with authentication for the other user."""
    with app.app_context():
        from flask_login import login_user
        from app.models import User
        
        # Find the other user
        user = User.query.filter_by(email='other@example.com').first()
        
        # Make sure the user exists
        assert user is not None, "Other test user not found in database"
        
        # Create a test client with the user logged in
        with client.session_transaction() as session:
            # Log in the user
            response = client.post('/login', data={
                'email': 'other@example.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # Check that the login was successful
            assert b'Login unsuccessful' not in response.data
        
        return client
