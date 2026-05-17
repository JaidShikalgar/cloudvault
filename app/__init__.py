# app/__init__.py
# This file creates the Flask app and connects all the pieces together

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# db is our database object - we'll use it everywhere to talk to the database
db = SQLAlchemy()

# login_manager handles user sessions (who is logged in, who isn't)
login_manager = LoginManager()

def create_app():
    """
    This function creates and returns the Flask app.
    Using a function (instead of just `app = Flask(...)`) is called
    the 'Application Factory Pattern' - it's a best practice.
    """
    
    # Create the Flask app
    # __name__ tells Flask where to look for templates and static files
    app = Flask(__name__)
    
    # Load our configuration from config.py
    app.config.from_object(Config)
    
    # Connect the database to our app
    db.init_app(app)
    
    # Connect the login manager to our app
    login_manager.init_app(app)
    
    # If someone tries to visit a page that needs login,
    # redirect them to the 'login' page (we'll create this route later)
    login_manager.login_view = 'auth.login'
    
    # Make the login message look nice
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import and register our route "blueprints"
    # Blueprints are like separate mini-apps we group related routes into
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.files import files as files_blueprint
    app.register_blueprint(files_blueprint)
    
    from app.profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint)
    
    # Import the main routes (homepage)
    from app import routes
    app.register_blueprint(routes.main)
    
    # Create all database tables if they don't exist yet
    with app.app_context():
        db.create_all()
    
    return app