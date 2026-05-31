# -*- coding: utf-8 -*-
# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
import os

db            = SQLAlchemy()
login_manager = LoginManager()
mail          = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view             = 'auth.login'
    login_manager.login_message          = 'Please login to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.files import files as files_blueprint
    app.register_blueprint(files_blueprint)

    from app.profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint)

    from app import routes
    app.register_blueprint(routes.main)

    with app.app_context():
        db.create_all()

    return app