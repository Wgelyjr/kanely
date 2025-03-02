from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import main, auth, kanban
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(kanban)

    with app.app_context():
        db.create_all()

    return app

from app import models
