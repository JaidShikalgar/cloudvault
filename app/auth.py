# -*- coding: utf-8 -*-
# app/auth.py

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, current_app)
from flask_login import (login_user, logout_user,
                         login_required, current_user)
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, mail
from app.models import User
import secrets
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)


# ═══════════════════════════════════════
# SIGNUP
# ═══════════════════════════════════════
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))

    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

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

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


# ═══════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.username}! 👋', 'success')
        return redirect(next_page or url_for('files.dashboard'))

    return render_template('login.html')


# ═══════════════════════════════════════
# LOGOUT
# ═══════════════════════════════════════
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ═══════════════════════════════════════
# FORGOT PASSWORD
# ═══════════════════════════════════════
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token        = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

            reset_url = url_for(
                'auth.reset_password',
                token=token,
                _external=True
            )

            try:
                send_reset_email(user.email, user.username, reset_url)
            except Exception as e:
                print(f"Email error: {e}")
                flash('Could not send email. Try again later.', 'danger')
                return render_template('forgot_password.html')

        flash(
            '📧 If that email exists, a reset link has been sent! '
            'Check your inbox and spam folder.',
            'success'
        )
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')

# ═══════════════════════════════════════
# RESET PASSWORD
# ═══════════════════════════════════════
@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('files.dashboard'))

    # Find user with this token
    user = User.query.filter_by(reset_token=token).first()

    # Check token exists and hasn't expired
    if not user or not user.reset_token_expiry:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if datetime.utcnow() > user.reset_token_expiry:
        # Token expired — clean it up
        user.reset_token        = None
        user.reset_token_expiry = None
        db.session.commit()
        flash('Reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        # Update password
        user.password_hash      = generate_password_hash(new_password)
        user.reset_token        = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('✅ Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


# ═══════════════════════════════════════
# SEND RESET EMAIL HELPER
# ═══════════════════════════════════════
def send_reset_email(to_email, username, reset_url):
    """Send password reset email using Flask-Mail"""
    msg = Message(
        subject='🔐 Reset Your CloudVault Password',
        recipients=[to_email]
    )

    # Plain text version
    msg.body = f"""
Hi {username},

You requested a password reset for your CloudVault account.

Click this link to reset your password:
{reset_url}

⏰ This link expires in 30 minutes.

If you did not request this, ignore this email.
Your password will not change.

— CloudVault Team
"""

    # HTML version (looks beautiful in email!)
    msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            background: #0a0a1a;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 560px;
            margin: 0 auto;
            background: #0f0f2e;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #4f8ef7, #8b5cf6);
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            color: white;
            margin: 0;
            font-size: 28px;
            font-weight: 800;
        }}
        .header p {{
            color: rgba(255,255,255,0.85);
            margin: 8px 0 0;
            font-size: 15px;
        }}
        .body {{
            padding: 40px 30px;
        }}
        .greeting {{
            color: #f0f0ff;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        .message {{
            color: #a0a0c0;
            font-size: 15px;
            line-height: 1.7;
            margin-bottom: 32px;
        }}
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, #4f8ef7, #8b5cf6);
            color: white !important;
            text-decoration: none;
            padding: 16px 40px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            text-align: center;
        }}
        .btn-wrapper {{
            text-align: center;
            margin-bottom: 32px;
        }}
        .expiry {{
            background: rgba(245,158,11,0.15);
            border: 1px solid rgba(245,158,11,0.3);
            border-radius: 8px;
            padding: 12px 16px;
            color: #fbbf24;
            font-size: 13px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .warning {{
            color: #606080;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 8px;
        }}
        .url-box {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 12px;
            word-break: break-all;
            font-size: 12px;
            color: #4f8ef7;
            margin-top: 8px;
        }}
        .footer {{
            background: rgba(255,255,255,0.03);
            padding: 20px 30px;
            text-align: center;
            color: #404060;
            font-size: 13px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☁️ CloudVault</h1>
            <p>Password Reset Request</p>
        </div>
        <div class="body">
            <p class="greeting">Hi {username}! 👋</p>
            <p class="message">
                We received a request to reset the password for your
                CloudVault account. Click the button below to create
                a new password.
            </p>
            <div class="btn-wrapper">
                <a href="{reset_url}" class="btn">
                    🔐 Reset My Password
                </a>
            </div>
            <div class="expiry">
                ⏰ This link expires in <strong>30 minutes</strong>
            </div>
            <p class="warning">
                If you didn't request a password reset, you can safely
                ignore this email. Your password will not change.
            </p>
            <p class="warning">
                If the button doesn't work, copy this link:
            </p>
            <div class="url-box">{reset_url}</div>
        </div>
        <div class="footer">
            ☁️ CloudVault — Your files, everywhere.<br>
            This is an automated message, please do not reply.
        </div>
    </div>
</body>
</html>
"""
    mail.send(msg)

