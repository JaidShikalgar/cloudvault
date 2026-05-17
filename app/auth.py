# app/auth.py
# Authentication routes: Signup, Login, Logout

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

# Create a blueprint named 'auth'
auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET  → Show the signup form
    POST → Process the form data (create account)
    """
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))
    
    if request.method == 'POST':
        # Get data from the form
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # --- Validation ---
        error = None
        
        if not username or not email or not password:
            error = 'All fields are required.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
        
        if error:
            flash(error, 'danger')
            return render_template('signup.html')
        
        # --- Create new user ---
        # generate_password_hash() converts "mypassword" to a safe hash like
        # "pbkdf2:sha256:260000$..." — we NEVER store plain text passwords!
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )
        
        # Save to database
        db.session.add(new_user)      # Stage the new user
        db.session.commit()            # Actually save to DB
        
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    # GET request - just show the form
    return render_template('signup.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Show the login form
    POST → Check credentials and log in
    """
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # check_password_hash() compares the entered password with the stored hash
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')
        
        # Log the user in (Flask-Login handles the session cookie)
        login_user(user, remember=remember)
        
        # If they were redirected here from another page, send them back there
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.username}! 👋', 'success')
        return redirect(next_page or url_for('files.dashboard'))
    
    return render_template('login.html')


@auth.route('/logout')
@login_required   # This decorator ensures only logged-in users can log out
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))