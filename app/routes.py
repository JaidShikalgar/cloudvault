# app/routes.py
# This handles the main homepage route

from flask import Blueprint, render_template
from flask_login import current_user

# Blueprint is like a "mini Flask app" for grouping routes
# 'main' is the name of this blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    This function runs when someone visits http://localhost:5000/
    If they're already logged in, we pass that info to the template
    """
    return render_template('index.html', user=current_user)