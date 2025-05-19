from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)

    # Load configuration from config.py
    app.config['SECRET_KEY'] = 'ghostly_secret_key'  # Replace with a secure key in production
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    # Initialize the database with the app
    db.init_app(app)

    # Import blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models after db is defined
    from .models import User, UserInteraction

    # Create database if it doesn't exist
    create_database(app)

    # Set up login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Redirect to login page if not logged in
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    # Check if database exists before creating
    if not path.exists('instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')