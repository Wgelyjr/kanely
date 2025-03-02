from app import create_app, db
from app.models import User, Board, Column, Card
import sqlite3

def update_database_schema():
    """Update the database schema with new tables and columns"""
    try:
        # Connect to the database
        conn = sqlite3.connect('instance/kanban.db')
        cursor = conn.cursor()
        
        # 1. Add dark_mode column to the user table if it doesn't exist
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        if 'dark_mode' not in user_columns:
            print("Adding dark_mode column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN dark_mode BOOLEAN DEFAULT 0")
            conn.commit()
            print("Column added successfully!")
        else:
            print("dark_mode column already exists.")
        
        # 2. Create board_shares table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='board_shares'")
        if not cursor.fetchone():
            print("Creating board_shares table...")
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
            print("board_shares table created successfully!")
        else:
            print("board_shares table already exists.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

if __name__ == '__main__':
    update_database_schema()
    
    # Create app context to test the database
    app = create_app()
    with app.app_context():
        # Verify the column exists
        user_count = User.query.count()
        print(f"Database has {user_count} users.")
        
        # Print all users and their dark_mode setting
        users = User.query.all()
        for user in users:
            print(f"User: {user.username}, Dark Mode: {user.dark_mode}")
