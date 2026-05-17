# -*- coding: utf-8 -*-
# app/profile.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

profile = Blueprint('profile', __name__)

@profile.route('/profile')
@login_required
def profile_page():
    from app.models import File

    total_files = File.query.filter_by(user_id=current_user.id).count()
    shared_files = File.query.filter_by(
        user_id=current_user.id, is_shared=True
    ).count()

    storage_used_mb = current_user.storage_used / (1024 * 1024)
    storage_limit_mb = 1024
    storage_percent = min((storage_used_mb / storage_limit_mb) * 100, 100)

    file_types = db.session.query(
        File.file_type, db.func.count(File.id)
    ).filter_by(user_id=current_user.id).group_by(File.file_type).all()

    return render_template('profile.html',
                           total_files=total_files,
                           shared_files=shared_files,
                           storage_used_mb=round(storage_used_mb, 2),
                           storage_percent=round(storage_percent, 1),
                           file_types=file_types)


@profile.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password     = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile.profile_page'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('profile.profile_page'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile.profile_page'))

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('✅ Password changed successfully!', 'success')
    return redirect(url_for('profile.profile_page'))