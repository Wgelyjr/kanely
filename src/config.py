import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///kanban.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
