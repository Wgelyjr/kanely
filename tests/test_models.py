import pytest
import sys
import os

from app.models import User, Board, Column, Card, board_shares
from sqlalchemy import and_


def test_user_creation(app):
    """also tests password hashing"""
    with app.app_context():
        # Create a user
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        
        # Check password hashing
        assert user.check_password('password') is True
        assert user.check_password('wrong_password') is False
        
        # Check string representation
        assert str(user) == "User('testuser', 'test@example.com')"


def test_board_creation(app, init_database):
    with app.app_context():
        # Get the test user
        user = User.query.filter_by(username='testuser').first()
        
        # Check if the board was created
        board = Board.query.filter_by(user_id=user.id).first()
        assert board is not None
        assert board.title == 'Test Board'
        
        # Check if the board is associated with the user
        assert board.owner == user
        
        # Check string representation
        assert str(board) == "Board('Test Board')"


def test_column_creation(app, init_database):
    with app.app_context():
        # Get the test board
        board = Board.query.filter_by(title='Test Board').first()
        
        # Check if columns were created
        columns = Column.query.filter_by(board_id=board.id).order_by(Column.position).all()
        assert len(columns) == 3
        assert columns[0].title == 'To Do'
        assert columns[1].title == 'In Progress'
        assert columns[2].title == 'Done'
        
        # Check if columns are associated with the board
        assert columns[0].board == board
        
        # Check string representation
        assert str(columns[0]) == "Column('To Do', position=0)"


def test_card_creation(app, init_database):
    with app.app_context():
        # Get the first column
        column = Column.query.filter_by(title='To Do').first()
        
        # Check if cards were created
        cards = Card.query.filter_by(column_id=column.id).order_by(Card.position).all()
        assert len(cards) == 2
        assert cards[0].title == 'Test Card 1'
        assert cards[1].title == 'Test Card 2'
        
        # Check if cards are associated with the column
        assert cards[0].column == column
        
        # Check string representation
        assert str(cards[0]) == "Card('Test Card 1', position=0)"


def test_board_sharing(app, init_database):
    with app.app_context():
        # Get the test users
        user1 = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='otheruser').first()
        
        # Get the test board
        board = Board.query.filter_by(title='Test Board').first()
        
        # Check if the board is shared with user2
        assert user2 in board.shared_with
        
        # Check if user2 can view but not edit the board
        assert board.can_view(user2) is True
        assert board.can_edit(user2) is False
        
        # Update the permission to allow editing
        stmt = board_shares.update().where(
            and_(
                board_shares.c.board_id == board.id,
                board_shares.c.user_id == user2.id
            )
        ).values(can_edit=True)
        init_database.session.execute(stmt)
        init_database.session.commit()
        
        # Check if user2 can now edit the board
        assert board.can_edit(user2) is True


def test_user_board_relationships(app, init_database):
    with app.app_context():
        # Get the test users
        user1 = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='otheruser').first()
        
        # Check if user1 owns the board
        assert len(user1.boards) == 1
        assert user1.boards[0].title == 'Test Board'
        
        # Check if user2 has the board shared with them
        assert len(user2.shared_boards) == 1
        assert user2.shared_boards[0].title == 'Test Board'


def test_board_owner_methods(app, init_database):
    with app.app_context():
        # Get the test users
        user1 = User.query.filter_by(username='testuser').first()
        user2 = User.query.filter_by(username='otheruser').first()
        
        # Get the test board
        board = Board.query.filter_by(title='Test Board').first()
        
        # Check if user1 is the owner
        assert board.is_owner(user1) is True
        assert board.is_owner(user2) is False
        
        # Check if user1 can view and edit
        assert board.can_view(user1) is True
        assert board.can_edit(user1) is True
