from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy.ext.associationproxy import association_proxy

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    dark_mode = db.Column(db.Boolean, default=False)
    boards = db.relationship('Board', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Board sharing association table
board_shares = db.Table('board_shares',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('board_id', db.Integer, db.ForeignKey('board.id'), primary_key=True),
    db.Column('can_edit', db.Boolean, default=False)
)

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    columns = db.relationship('Column', backref='board', lazy=True, cascade='all, delete-orphan')
    
    # Users who have access to this board (many-to-many)
    shared_with = db.relationship('User', 
                                 secondary=board_shares,
                                 lazy='subquery',
                                 backref=db.backref('shared_boards', lazy=True))
    
    def __repr__(self):
        return f"Board('{self.title}')"
    
    def is_owner(self, user):
        return self.user_id == user.id
    
    def can_edit(self, user):
        if self.is_owner(user):
            return True
        
        # Check if the board is shared with the user with edit permissions
        share = db.session.query(board_shares).filter_by(
            user_id=user.id, 
            board_id=self.id
        ).first()
        
        return share is not None and share.can_edit
    
    def can_view(self, user):
        if self.is_owner(user):
            return True
        
        # Check if the board is shared with the user
        share = db.session.query(board_shares).filter_by(
            user_id=user.id, 
            board_id=self.id
        ).first()
        
        return share is not None

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    cards = db.relationship('Card', backref='column', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Column('{self.title}', position={self.position})"

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    column_id = db.Column(db.Integer, db.ForeignKey('column.id'), nullable=False)
    
    def __repr__(self):
        return f"Card('{self.title}', position={self.position})"
