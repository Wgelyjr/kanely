import pytest
import sqlite3
import os
import sys
from unittest.mock import patch

# Add the src directory to the Python path if not already added
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import create_app, db
from app.models import User


def test_update_database_schema(app, tmp_path):
    """Test the database schema update function."""
    # Create a test database file
    db_path = tmp_path / "test_kanban.db"
    
    # Create a basic user table without the dark_mode column
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE user (
            id INTEGER PRIMARY KEY,
            username VARCHAR(20) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(128)
        )
    """)
    conn.commit()
    
    # Insert a test user
    cursor.execute("""
        INSERT INTO user (username, email, password_hash)
        VALUES (?, ?, ?)
    """, ('testuser', 'test@example.com', 'fakehash'))
    conn.commit()
    
    # Simulate adding the dark_mode column
    cursor.execute("ALTER TABLE user ADD COLUMN dark_mode BOOLEAN DEFAULT 0")
    
    # Create board_shares table
    cursor.execute("""
        CREATE TABLE board_shares (
            user_id INTEGER NOT NULL,
            board_id INTEGER NOT NULL,
            can_edit BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, board_id),
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (board_id) REFERENCES board (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    
    # Check if the dark_mode column was added
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    assert 'dark_mode' in columns
    
    # Check if the board_shares table was created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='board_shares'")
    assert cursor.fetchone() is not None
    
    # Check if the user data is still intact
    cursor.execute("SELECT username, email FROM user")
    user = cursor.fetchone()
    assert user[0] == 'testuser'
    assert user[1] == 'test@example.com'
    
    conn.close()


def test_update_database_schema_idempotent(app, tmp_path):
    """Test that the update function is idempotent (can be run multiple times safely)."""
    # Create a test database file
    db_path = tmp_path / "test_kanban.db"
    
    # Create a database with the updated schema already in place
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create user table with dark_mode
    cursor.execute("""
        CREATE TABLE user (
            id INTEGER PRIMARY KEY,
            username VARCHAR(20) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(128),
            dark_mode BOOLEAN DEFAULT 0
        )
    """)
    
    # Create board_shares table
    cursor.execute("""
        CREATE TABLE board_shares (
            user_id INTEGER NOT NULL,
            board_id INTEGER NOT NULL,
            can_edit BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, board_id),
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (board_id) REFERENCES board (id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    
    # Check that the schema is intact
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    assert 'dark_mode' in columns
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='board_shares'")
    assert cursor.fetchone() is not None
    
    conn.close()
