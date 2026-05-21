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
        # Log error but DON'T crash — show success anyway
                print(f"Email error (non-fatal): {e}")

        # Always show success — security best practice
        flash(
            '📧 If that email exists, a reset link has been sent! '
            'Check your inbox and spam folder.',
            'success'
        )
        # Redirect immediately — don't wait for email
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
    """
    Send password reset email using SendGrid API.
    More reliable than Gmail SMTP on cloud servers.
    """
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content

    try:
        api_key  = current_app.config.get('SENDGRID_API_KEY')
        from_email = current_app.config.get('MAIL_FROM') or \
                     current_app.config.get('MAIL_USERNAME')

        if not api_key:
            print("❌ SendGrid API key not found!")
            raise Exception("SendGrid API key not configured")

        sg = sendgrid.SendGridAPIClient(api_key=api_key)

        # Plain text
        plain_text = f"""
Hi {username},

Reset your CloudVault password:
{reset_url}

This link expires in 30 minutes.

If you didn't request this, ignore this email.

— CloudVault Team
"""

        # HTML email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f0f2ff;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 560px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(79,142,247,0.15);
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
            color: rgba(255,255,255,0.9);
            margin: 8px 0 0;
            font-size: 15px;
        }}
        .body {{
            padding: 40px 30px;
        }}
        .greeting {{
            color: #1a1a3e;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
        }}
        .message {{
            color: #4a4a6a;
            font-size: 15px;
            line-height: 1.7;
            margin-bottom: 28px;
        }}
        .btn-wrapper {{
            text-align: center;
            margin-bottom: 28px;
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
        }}
        .expiry {{
            background: #fff8e6;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 12px 16px;
            color: #b45309;
            font-size: 13px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .warning {{
            color: #9090a0;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 8px;
        }}
        .url-box {{
            background: #f0f2ff;
            border: 1px solid #c7d2fe;
            border-radius: 8px;
            padding: 12px;
            word-break: break-all;
            font-size: 12px;
            color: #4f8ef7;
            margin-top: 8px;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px 30px;
            text-align: center;
            color: #9090a0;
            font-size: 13px;
            border-top: 1px solid #e8eaff;
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
                We received a request to reset your CloudVault password.
                Click the button below to create a new password.
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
                If you didn't request this, you can safely ignore
                this email. Your password will not change.
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

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject='🔐 Reset Your CloudVault Password',
            html_content=html_content
        )
        message.plain_text_content = plain_text

        response = sg.send(message)
        print(f"✅ SendGrid email sent! Status: {response.status_code}")
        return True

    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        raise e