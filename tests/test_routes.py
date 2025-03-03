import pytest
import json
import sys
import os

from app.models import User, Board, Column, Card
from app import db


def test_home_page(client):
    """Test the home page route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Kanely' in response.data or b'Login' in response.data


def test_register_page(client):
    """Test the register page route."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data


def test_login_page(client):
    """Test the login page route."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_user(client, app):
    with app.app_context():
        # Check that the user doesn't exist yet
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is None
        
        # Register a new user
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password',
            'confirm_password': 'password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Your account has been created' in response.data or b'You can now log in' in response.data
        
        # Check that the user was created
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.username == 'newuser'
        assert user.check_password('password') is True


def test_login_user(client, init_database):
    # login with correct credentials - from test_config.py
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Check that we're redirected to the boards page
    assert b'My Boards' in response.data or b'Test Board' in response.data


def test_user_logout(auth_client):
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data or b'Register' in response.data


def test_boards_page(auth_client, init_database):
    """Test the GENERIC boards page route"""
    response = auth_client.get('/boards')
    assert response.status_code == 200
    assert b'My Boards' in response.data
    assert b'Test Board' in response.data


def test_board_page_route(auth_client, init_database):
    """Tests a SPECIFIC board route"""
    with auth_client.application.app_context():
        # Get the board ID
        board = Board.query.filter_by(title='Test Board').first()
        
        response = auth_client.get(f'/board/{board.id}')
        assert response.status_code == 200
        assert b'Test Board' in response.data
        assert b'To Do' in response.data
        assert b'In Progress' in response.data
        assert b'Done' in response.data
        assert b'Test Card 1' in response.data
        assert b'Test Card 2' in response.data


def test_create_board(auth_client, app):
    with app.app_context():
        # Count boards before
        board_count = Board.query.count()
        
        # Create a new board
        response = auth_client.post('/board/new', data={
            'title': 'New Test Board'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Your board has been created' in response.data
        
        # Check that the board was created
        assert Board.query.count() == board_count + 1
        board = Board.query.filter_by(title='New Test Board').first()
        assert board is not None
        
        # Check that default columns were created
        columns = Column.query.filter_by(board_id=board.id).order_by(Column.position).all()
        assert len(columns) == 3
        assert columns[0].title == 'To Do'
        assert columns[1].title == 'In Progress'
        assert columns[2].title == 'Done'


def test_create_column(auth_client, app, init_database):
    with app.app_context():
        # Get the board ID
        board = Board.query.filter_by(title='Test Board').first()
        
        # Count columns before
        column_count = Column.query.filter_by(board_id=board.id).count()
        
        # Create a new column
        response = auth_client.post(f'/board/{board.id}/column/new', data={
            'title': 'New Column'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Column added' in response.data
        
        # Check that the column was created
        assert Column.query.filter_by(board_id=board.id).count() == column_count + 1
        column = Column.query.filter_by(board_id=board.id, title='New Column').first()
        assert column is not None
        assert column.position == 3  # Should be after the existing columns


def test_create_card(auth_client, app, init_database):
    with app.app_context():
        # Get the column ID
        column = Column.query.filter_by(title='To Do').first()
        
        # Count cards before
        card_count = Card.query.filter_by(column_id=column.id).count()
        
        # Create a new card
        response = auth_client.post(f'/column/{column.id}/card/new', data={
            'title': 'New Card',
            'description': 'New Card Description'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card added' in response.data
        
        # Check that the card was created
        assert Card.query.filter_by(column_id=column.id).count() == card_count + 1
        card = Card.query.filter_by(column_id=column.id, title='New Card').first()
        assert card is not None
        assert card.description == 'New Card Description'
        assert card.position == 2  # Should be after the existing cards


def test_move_card(auth_client, app, init_database):
    with app.app_context():
        # Get the card and columns
        card = Card.query.filter_by(title='Test Card 1').first()
        source_column = Column.query.filter_by(title='To Do').first()
        target_column = Column.query.filter_by(title='In Progress').first()
        
        # Move the card to a different column
        response = auth_client.post(f'/card/{card.id}/move', 
                                   json={
                                       'columnId': target_column.id,
                                       'position': 0
                                   },
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Check that the card was moved
        card = db.session.get(Card, card.id)
        assert card.column_id == target_column.id
        assert card.position == 0


def test_delete_card(auth_client, app, init_database):
    with app.app_context():
        # Get the card
        card = Card.query.filter_by(title='Test Card 1').first()
        board_id = card.column.board_id
        
        # Delete the card
        response = auth_client.post(f'/card/{card.id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Card has been deleted' in response.data
        
        # Check that the card was deleted
        card = Card.query.filter_by(title='Test Card 1').first()
        assert card is None


def test_delete_column(auth_client, app, init_database):
    with app.app_context():
        # Get the column
        column = Column.query.filter_by(title='To Do').first()
        board_id = column.board_id
        
        # Delete the column
        response = auth_client.post(f'/column/{column.id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Column has been deleted' in response.data
        
        # Check that the column was deleted
        column = Column.query.filter_by(title='To Do').first()
        assert column is None
        
        # Check that the cards in the column were also deleted
        cards = Card.query.filter_by(column_id=column.id).all() if column else []
        assert len(cards) == 0


def test_delete_board(auth_client, app, init_database):
    """Test deleting a board."""
    with app.app_context():
        # Get the board
        board = Board.query.filter_by(title='Test Board').first()
        
        # Delete the board
        response = auth_client.post(f'/board/{board.id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Your board has been deleted' in response.data
        
        # Check that the board was deleted
        board = Board.query.filter_by(title='Test Board').first()
        assert board is None
        
        # Check that the columns and cards were also deleted
        columns = Column.query.filter_by(board_id=board.id).all() if board else []
        assert len(columns) == 0
        
        for column in columns:
            cards = Card.query.filter_by(column_id=column.id).all()
            assert len(cards) == 0


def test_share_board_page(auth_client, init_database):
    """Test the share board page."""
    with auth_client.application.app_context():
        # Get the board ID
        board = Board.query.filter_by(title='Test Board').first()
        
        response = auth_client.get(f'/board/{board.id}/share')
        assert response.status_code == 200
        assert b'Share' in response.data
        assert b'Test Board' in response.data


def test_share_board(auth_client, app, init_database):
    """Test sharing a board with another user."""
    with app.app_context():
        # Create a new user to share with
        user = User(username='shareuser', email='share@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Get the board ID
        board = Board.query.filter_by(title='Test Board').first()
        
        # Share the board
        response = auth_client.post(f'/board/{board.id}/share', data={
            'user_email': 'share@example.com',
            'permission': 'edit'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Board shared with shareuser' in response.data
        
        # Check that the board is shared
        user = User.query.filter_by(email='share@example.com').first()
        assert board in user.shared_boards
        
        # Check that the user has edit permission
        assert board.can_edit(user) is True


def test_update_share_permission(auth_client, app, init_database):
    """Test updating share permissions."""
    with app.app_context():
        # Get the board and user
        board = Board.query.filter_by(title='Test Board').first()
        user = User.query.filter_by(email='other@example.com').first()
        
        # Initially, the user should have view-only permission
        assert board.can_view(user) is True
        assert board.can_edit(user) is False
        
        # Update to edit permission
        response = auth_client.post(f'/board/{board.id}/user/{user.id}/permission', data={
            'permission': 'edit'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Permission updated' in response.data
        
        # Check that the permission was updated
        assert board.can_edit(user) is True


def test_remove_share(auth_client, app, init_database):
    """Test removing a share."""
    with app.app_context():
        # Get the board and user
        board = Board.query.filter_by(title='Test Board').first()
        user = User.query.filter_by(email='other@example.com').first()
        
        # Initially, the board should be shared with the user
        assert user in board.shared_with
        
        # Remove the share
        response = auth_client.post(f'/board/{board.id}/user/{user.id}/remove', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'User access has been removed' in response.data
        
        # Check that the share was removed
        assert user not in board.shared_with


def test_settings_page(auth_client):
    """Test the settings page."""
    response = auth_client.get('/settings')
    assert response.status_code == 200
    assert b'User Settings' in response.data
    assert b'Dark Mode' in response.data


def test_update_settings(auth_client, app, init_database):
    """Test updating user settings."""
    with app.app_context():
        # Get the user
        user = User.query.filter_by(email='test@example.com').first()
        
        # Initially, dark mode should be off
        assert user.dark_mode is False
        
        # Update settings to enable dark mode
        response = auth_client.post('/settings', data={
            'dark_mode': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Your settings have been updated' in response.data
        
        # Check that the setting was updated
        user = User.query.filter_by(email='test@example.com').first()
        assert user.dark_mode is True


def test_unauthorized_access(client, init_database):
    """Test unauthorized access to protected routes."""
    # Try to access boards page without login
    response = client.get('/boards', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page' in response.data
    
    # Try to access settings page without login
    response = client.get('/settings', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page' in response.data


def test_board_access_control(app, init_database):
    """Test board access control."""
    with app.app_context():
        # Get the board and users
        board = Board.query.filter_by(title='Test Board').first()
        owner = User.query.filter_by(email='test@example.com').first()
        viewer = User.query.filter_by(email='other@example.com').first()
        
        # Create a client for a third user who doesn't have access
        third_user = User(username='thirduser', email='third@example.com')
        third_user.set_password('password')
        db.session.add(third_user)
        db.session.commit()
        
        # Create a test client for the third user
        with app.test_client() as third_client:
            # Login as the third user
            third_client.post('/login', data={
                'email': 'third@example.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # Try to access the board
            response = third_client.get(f'/board/{board.id}')
            assert response.status_code == 403  # Forbidden
            
            # Try to modify the board
            response = third_client.post(f'/board/{board.id}/column/new', data={
                'title': 'Unauthorized Column'
            })
            assert response.status_code == 403  # Forbidden
