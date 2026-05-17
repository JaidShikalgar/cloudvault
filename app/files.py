# -*- coding: utf-8 -*-
# app/files.py

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, send_file, jsonify, current_app, Response)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import File, User
import os, uuid, secrets, io
from datetime import datetime
import requests as http_requests

files = Blueprint('files', __name__)

ALLOWED_EXTENSIONS = {
    'txt','pdf','doc','docx','xls','xlsx','csv','ppt','pptx',
    'jpg','jpeg','png','gif','svg','webp',
    'mp4','avi','mov','mkv','mp3','wav','flac',
    'zip','rar','7z','tar','py','js','html','css','json','md'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_supabase():
    """Create and return Supabase client"""
    from supabase import create_client
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_KEY']
    
    # DEBUG - print what we actually have
    print(f"DEBUG ENV - URL: '{url}'")
    print(f"DEBUG ENV - KEY starts with: '{str(key)[:20] if key else None}'")
    
    if not url or not key:
        print("DEBUG: url or key is empty!")
        return None
    if 'your_supabase' in str(url):
        print("DEBUG: url still has placeholder text!")
        return None
        
    return create_client(url, key)

def get_preview_url(stored_name):
    """Get a temporary preview URL for image files"""
    try:
        from flask import current_app
        supabase = get_supabase()
        if not supabase:
            return None
        bucket = current_app.config['SUPABASE_BUCKET']
        response = supabase.storage.from_(bucket).create_signed_url(
            path=stored_name,
            expires_in=3600  # 1 hour
        )
        if isinstance(response, dict):
            return (response.get('signedURL') or 
                    response.get('signedUrl') or 
                    response.get('signed_url'))
        elif hasattr(response, 'signed_url'):
            return response.signed_url
    except Exception as e:
        print(f"Preview URL error: {e}")
    return None

@files.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'date')  # date, name, size
    file_type_filter = request.args.get('type', 'all')

    query = File.query.filter_by(user_id=current_user.id)

    # Search filter
    if search_query:
        query = query.filter(File.filename.ilike(f'%{search_query}%'))

    # File type filter
    image_types = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']
    doc_types = ['pdf', 'doc', 'docx', 'txt', 'md']
    video_types = ['mp4', 'avi', 'mov', 'mkv']
    
    if file_type_filter == 'images':
        query = query.filter(File.file_type.in_(image_types))
    elif file_type_filter == 'documents':
        query = query.filter(File.file_type.in_(doc_types))
    elif file_type_filter == 'videos':
        query = query.filter(File.file_type.in_(video_types))

    # Sorting
    if sort_by == 'name':
        query = query.order_by(File.filename.asc())
    elif sort_by == 'size':
        query = query.order_by(File.file_size.desc())
    else:
        query = query.order_by(File.uploaded_at.desc())

    all_files = query.all()

    # Generate preview URLs for images
    preview_urls = {}
    for f in all_files:
        if f.file_type.lower() in image_types:
            preview_urls[f.id] = get_preview_url(f.stored_name)

    recent_files = File.query.filter_by(user_id=current_user.id)\
                             .order_by(File.uploaded_at.desc())\
                             .limit(6).all()

    # Recent file previews
    for f in recent_files:
        if f.file_type.lower() in image_types and f.id not in preview_urls:
            preview_urls[f.id] = get_preview_url(f.stored_name)

    storage_used_mb = current_user.storage_used / (1024 * 1024)
    storage_limit_mb = 1024
    storage_percent = min((storage_used_mb / storage_limit_mb) * 100, 100)

    # File counts by type for sidebar
    total_images = File.query.filter_by(user_id=current_user.id)\
                             .filter(File.file_type.in_(image_types)).count()
    total_docs = File.query.filter_by(user_id=current_user.id)\
                           .filter(File.file_type.in_(doc_types)).count()
    total_videos = File.query.filter_by(user_id=current_user.id)\
                             .filter(File.file_type.in_(video_types)).count()

    return render_template('dashboard.html',
                           files=all_files,
                           recent_files=recent_files,
                           preview_urls=preview_urls,
                           search_query=search_query,
                           sort_by=sort_by,
                           file_type_filter=file_type_filter,
                           storage_used_mb=round(storage_used_mb, 2),
                           storage_limit_mb=storage_limit_mb,
                           storage_percent=round(storage_percent, 1),
                           total_images=total_images,
                           total_docs=total_docs,
                           total_videos=total_videos)

@files.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('files.dashboard'))

    uploaded_files = request.files.getlist('file')
    success_count = 0

    for file in uploaded_files:
        if file.filename == '':
            continue
        if not allowed_file(file.filename):
            flash(f'File type not allowed: {file.filename}', 'danger')
            continue

        original_name = file.filename
        safe_name = secure_filename(original_name)
        extension = safe_name.rsplit('.', 1)[1].lower() if '.' in safe_name else 'bin'
        unique_name = f"{current_user.id}/{uuid.uuid4().hex}.{extension}"
        file_content = file.read()
        file_size = len(file_content)
        mime = file.content_type or 'application/octet-stream'

        supabase = get_supabase()
        print(f"DEBUG upload: supabase={'connected' if supabase else 'None'}")

        if supabase:
            try:
                bucket = current_app.config['SUPABASE_BUCKET']
                supabase.storage.from_(bucket).upload(
                    path=unique_name,
                    file=file_content,
                    file_options={"content-type": mime}
                )
                print(f"DEBUG: Uploaded to Supabase: {unique_name}")
            except Exception as e:
                flash(f'Upload failed for {original_name}: {str(e)}', 'danger')
                print(f"DEBUG upload error: {e}")
                continue
        else:
            upload_folder = os.path.join(
                current_app.root_path, 'static', 'uploads', str(current_user.id)
            )
            os.makedirs(upload_folder, exist_ok=True)
            local_filename = unique_name.replace('/', '_')
            with open(os.path.join(upload_folder, local_filename), 'wb') as f:
                f.write(file_content)
            print(f"DEBUG: Saved locally: {local_filename}")

        new_file = File(
            filename=original_name,
            stored_name=unique_name,
            file_size=file_size,
            file_type=extension,
            mime_type=mime,
            user_id=current_user.id
        )
        db.session.add(new_file)
        current_user.storage_used += file_size
        success_count += 1

    if success_count > 0:
        db.session.commit()
        flash(f'✅ {success_count} file(s) uploaded successfully!', 'success')

    return redirect(url_for('files.dashboard'))


@files.route('/download/<int:file_id>')
@login_required
def download(file_id):
    """Download a file"""
    print(f"\n--- DOWNLOAD STARTED for file_id: {file_id} ---")
    
    file = File.query.get_or_404(file_id)
    print(f"DEBUG: File found: {file.filename}, stored as: {file.stored_name}")

    if file.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('files.dashboard'))

    supabase = get_supabase()
    print(f"DEBUG: Supabase client: {'connected' if supabase else 'None - using local'}")

    if supabase:
        bucket = current_app.config['SUPABASE_BUCKET']
        print(f"DEBUG: Using bucket: {bucket}")
        
        # --- Try Method 1: Create signed URL and redirect ---
        try:
            print("DEBUG: Trying signed URL method...")
            response = supabase.storage.from_(bucket).create_signed_url(
                path=file.stored_name,
                expires_in=300  # 5 minutes
            )
            print(f"DEBUG: Signed URL response: {response}")
            
            # Handle different response formats
            signed_url = None
            if isinstance(response, dict):
                signed_url = response.get('signedURL') or response.get('signedUrl') or response.get('signed_url')
            elif hasattr(response, 'signed_url'):
                signed_url = response.signed_url
            
            if signed_url:
                print(f"DEBUG: Got signed URL, redirecting...")
                return redirect(signed_url)
            else:
                print(f"DEBUG: No signed URL in response: {response}")
        except Exception as e:
            print(f"DEBUG: Signed URL method failed: {e}")

        # --- Try Method 2: Direct download into memory ---
        try:
            print("DEBUG: Trying direct download method...")
            data = supabase.storage.from_(bucket).download(file.stored_name)
            print(f"DEBUG: Downloaded {len(data)} bytes")
            return send_file(
                io.BytesIO(data),
                as_attachment=True,
                download_name=file.filename,
                mimetype=file.mime_type or 'application/octet-stream'
            )
        except Exception as e:
            print(f"DEBUG: Direct download failed: {e}")

        # --- Try Method 3: Get public URL (if bucket is public) ---
        try:
            print("DEBUG: Trying public URL method...")
            public_url = supabase.storage.from_(bucket).get_public_url(file.stored_name)
            print(f"DEBUG: Public URL: {public_url}")
            if public_url:
                return redirect(public_url)
        except Exception as e:
            print(f"DEBUG: Public URL method failed: {e}")

        print("DEBUG: ALL download methods failed!")
        flash('Download failed. Check terminal for details.', 'danger')
        return redirect(url_for('files.dashboard'))

    else:
        # Local fallback
        print("DEBUG: Using local storage fallback")
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        local_path = os.path.join(upload_folder, file.stored_name.replace('/', '_'))
        print(f"DEBUG: Looking for file at: {local_path}")
        if os.path.exists(local_path):
            return send_file(local_path, as_attachment=True, download_name=file.filename)
        flash('File not found on server.', 'danger')
        return redirect(url_for('files.dashboard'))


@files.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('files.dashboard'))

    supabase = get_supabase()
    if supabase:
        try:
            bucket = current_app.config['SUPABASE_BUCKET']
            supabase.storage.from_(bucket).remove([file.stored_name])
        except Exception as e:
            print(f'Supabase delete error: {e}')
    else:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        local_path = os.path.join(upload_folder, file.stored_name.replace('/', '_'))
        if os.path.exists(local_path):
            os.remove(local_path)

    current_user.storage_used = max(0, current_user.storage_used - file.file_size)
    db.session.delete(file)
    db.session.commit()
    flash(f'🗑️ "{file.filename}" deleted.', 'success')
    return redirect(url_for('files.dashboard'))


@files.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if file.is_shared:
        file.is_shared = False
        file.share_token = None
        db.session.commit()
        return jsonify({'shared': False})
    else:
        file.share_token = secrets.token_urlsafe(32)
        file.is_shared = True
        db.session.commit()
        share_url = url_for('files.shared_file', token=file.share_token, _external=True)
        return jsonify({'shared': True, 'share_url': share_url})


@files.route('/shared/<token>')
def shared_file(token):
    file = File.query.filter_by(share_token=token, is_shared=True).first_or_404()
    return render_template('shared.html', file=file)


@files.route('/shared/download/<token>')
def download_shared(token):
    file = File.query.filter_by(share_token=token, is_shared=True).first_or_404()
    supabase = get_supabase()

    if supabase:
        bucket = current_app.config['SUPABASE_BUCKET']
        try:
            response = supabase.storage.from_(bucket).create_signed_url(
                path=file.stored_name, expires_in=300
            )
            signed_url = None
            if isinstance(response, dict):
                signed_url = response.get('signedURL') or response.get('signedUrl') or response.get('signed_url')
            elif hasattr(response, 'signed_url'):
                signed_url = response.signed_url
            if signed_url:
                return redirect(signed_url)
        except Exception as e:
            print(f"Shared download signed URL error: {e}")
        try:
            data = supabase.storage.from_(bucket).download(file.stored_name)
            return send_file(io.BytesIO(data), as_attachment=True,
                           download_name=file.filename,
                           mimetype=file.mime_type or 'application/octet-stream')
        except Exception as e:
            print(f"Shared download direct error: {e}")

        flash('Download failed.', 'danger')
        return redirect(url_for('files.shared_file', token=token))
    else:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        local_path = os.path.join(upload_folder, file.stored_name.replace('/', '_'))
        if os.path.exists(local_path):
            return send_file(local_path, as_attachment=True, download_name=file.filename)
        flash('File not found.', 'danger')
        return redirect(url_for('files.shared_file', token=token))