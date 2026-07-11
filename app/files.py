# -*- coding: utf-8 -*-
# app/files.py

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, send_file, jsonify, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import File
from app.storage import upload_file, download_file, delete_file, get_presigned_url
import os, uuid, secrets, io

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


# ═══════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════
@files.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    sort_by      = request.args.get('sort', 'date')
    file_type    = request.args.get('type', 'all')

    query = File.query.filter_by(user_id=current_user.id)

    # Search
    if search_query:
        query = query.filter(File.filename.ilike(f'%{search_query}%'))

    # File type categories
    image_types = ['jpg','jpeg','png','gif','svg','webp']
    doc_types   = ['pdf','doc','docx','xls','xlsx','ppt','pptx','txt','csv']
    video_types = ['mp4','avi','mov','mkv']
    audio_types = ['mp3','wav','flac']

    # Filter by type
    if file_type == 'image':
        query = query.filter(File.file_type.in_(image_types))
    elif file_type == 'document':
        query = query.filter(File.file_type.in_(doc_types))
    elif file_type == 'video':
        query = query.filter(File.file_type.in_(video_types))
    elif file_type == 'audio':
        query = query.filter(File.file_type.in_(audio_types))

    # Sort
    if sort_by == 'name':
        query = query.order_by(File.filename.asc())
    elif sort_by == 'size':
        query = query.order_by(File.file_size.desc())
    else:
        query = query.order_by(File.uploaded_at.desc())

    all_files    = query.all()
    recent_files = File.query.filter_by(user_id=current_user.id)\
                             .order_by(File.uploaded_at.desc())\
                             .limit(12).all()

    # Storage — now 10GB with B2
    storage_limit_mb = current_app.config.get('STORAGE_LIMIT_MB', 10240)
    storage_used_mb  = current_user.storage_used / (1024 * 1024)
    storage_percent  = min((storage_used_mb / storage_limit_mb) * 100, 100)

    # File counts for sidebar filters
    total       = File.query.filter_by(user_id=current_user.id).count()
    image_count = File.query.filter_by(user_id=current_user.id)\
                            .filter(File.file_type.in_(image_types)).count()
    doc_count   = File.query.filter_by(user_id=current_user.id)\
                            .filter(File.file_type.in_(doc_types)).count()
    video_count = File.query.filter_by(user_id=current_user.id)\
                            .filter(File.file_type.in_(video_types)).count()

    return render_template('dashboard.html',
                           files=all_files,
                           recent_files=recent_files,
                           search_query=search_query,
                           sort_by=sort_by,
                           file_type=file_type,
                           storage_used_mb=round(storage_used_mb, 2),
                           storage_limit_mb=storage_limit_mb,
                           storage_percent=round(storage_percent, 1),
                           total_count=total,
                           image_count=image_count,
                           doc_count=doc_count,
                           video_count=video_count)

# ═══════════════════════════════════════
# UPLOAD
# ═══════════════════════════════════════
@files.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('files.dashboard'))

    uploaded_files = request.files.getlist('file')
    success_count  = 0

    for file in uploaded_files:
        # Skip empty files
        if file.filename == '':
            continue

        # Check allowed extension
        if not allowed_file(file.filename):
            flash(f'File type not allowed: {file.filename}', 'danger')
            continue

        # Create safe unique filename
        original_name = file.filename
        safe_name     = secure_filename(original_name)
        extension     = safe_name.rsplit('.', 1)[1].lower() \
                        if '.' in safe_name else 'bin'
        unique_name   = f"{current_user.id}/{uuid.uuid4().hex}.{extension}"

        # Read file into memory
        file_content = file.read()
        file_size    = len(file_content)
        mime         = file.content_type or 'application/octet-stream'

        # ── Upload to B2 → Supabase → Local ──
        # upload_file() tries each backend automatically
        backend = upload_file(file_content, unique_name, mime)

        # If all cloud storage failed, save locally
        if backend == 'local':
            folder = os.path.join(
                current_app.root_path, 'static',
                'uploads', str(current_user.id)
            )
            os.makedirs(folder, exist_ok=True)
            fname = unique_name.split('/')[-1]
            with open(os.path.join(folder, fname), 'wb') as f:
                f.write(file_content)

        # Save file record to database
        new_file = File(
            filename=original_name,
            stored_name=unique_name,
            file_size=file_size,
            file_type=extension,
            mime_type=mime,
            user_id=current_user.id,
            storage_backend=backend
        )
        db.session.add(new_file)

        # Update user storage usage
        current_user.storage_used += file_size
        success_count += 1

    if success_count > 0:
        db.session.commit()
        flash(f'✅ {success_count} file(s) uploaded successfully!', 'success')

    return redirect(url_for('files.dashboard'))


# ═══════════════════════════════════════
# DOWNLOAD
# ═══════════════════════════════════════
@files.route('/download/<int:file_id>')
@login_required
def download(file_id):
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('files.dashboard'))

    backend = getattr(file, 'storage_backend', 'b2') or 'b2'

    print(f"DEBUG download: file={file.filename}, backend={backend}")

    # Always stream through server
    # NEVER redirect to presigned URL for downloads
    # (presigned URL causes the browser tab flash)
    data = download_file(file.stored_name, backend)

    if data:
        print(f"DEBUG: Got {len(data)} bytes, sending as attachment")
        response = send_file(
            io.BytesIO(data),
            as_attachment=True,
            download_name=file.filename,
            mimetype='application/octet-stream'
        )
        # Extra headers to force download
        response.headers['Content-Disposition'] = \
            f'attachment; filename="{file.filename}"'
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    # Local fallback
    local_path = os.path.join(
        current_app.root_path, 'static', 'uploads',
        str(file.user_id),
        file.stored_name.split('/')[-1]
    )
    if os.path.exists(local_path):
        return send_file(
            local_path,
            as_attachment=True,
            download_name=file.filename,
            mimetype='application/octet-stream'
        )

    flash('File not found.', 'danger')
    return redirect(url_for('files.dashboard'))
# ═══════════════════════════════════════
# DELETE
# ═══════════════════════════════════════
@files.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('files.dashboard'))

    backend = getattr(file, 'storage_backend', 'b2') or 'b2'

    # Delete from cloud storage
    delete_file(file.stored_name, backend)

    # Delete local file if exists
    local_path = os.path.join(
        current_app.root_path, 'static', 'uploads',
        str(file.user_id), file.stored_name.split('/')[-1]
    )
    if os.path.exists(local_path):
        os.remove(local_path)

    # Update storage usage and remove DB record
    current_user.storage_used = max(
        0, current_user.storage_used - file.file_size
    )
    db.session.delete(file)
    db.session.commit()

    flash(f'🗑️ "{file.filename}" deleted successfully.', 'success')
    return redirect(url_for('files.dashboard'))


# ═══════════════════════════════════════
# SHARE
# ═══════════════════════════════════════
@files.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share(file_id):
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if file.is_shared:
        # Turn OFF sharing
        file.is_shared   = False
        file.share_token = None
        db.session.commit()
        return jsonify({'shared': False})
    else:
        # Turn ON sharing — generate unique public token
        file.share_token = secrets.token_urlsafe(32)
        file.is_shared   = True
        db.session.commit()
        share_url = url_for(
            'files.shared_file',
            token=file.share_token,
            _external=True
        )
        return jsonify({'shared': True, 'share_url': share_url})


# ═══════════════════════════════════════
# SHARED FILE PAGE (public — no login)
# ═══════════════════════════════════════
@files.route('/shared/<token>')
def shared_file(token):
    file = File.query.filter_by(
        share_token=token, is_shared=True
    ).first_or_404()
    return render_template('shared.html', file=file)


# ═══════════════════════════════════════
# DOWNLOAD SHARED FILE (public — no login)
# ═══════════════════════════════════════
@files.route('/shared/download/<token>')
def download_shared(token):
    file = File.query.filter_by(
        share_token=token, is_shared=True
    ).first_or_404()

    backend = getattr(file, 'storage_backend', 'b2') or 'b2'

    # Presigned URL
    url = get_presigned_url(file.stored_name, backend)
    if url:
        return redirect(url)

    # Direct download
    data = download_file(file.stored_name, backend)
    if data:
        return send_file(
            io.BytesIO(data),
            as_attachment=True,
            download_name=file.filename,
            mimetype=file.mime_type or 'application/octet-stream'
        )

    flash('File not found.', 'danger')
    return redirect(url_for('files.shared_file', token=token))


# ═══════════════════════════════════════
# IMAGE PREVIEW (returns signed URL)
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# TEST B2 CONNECTION (temporary route)
# ═══════════════════════════════════════
@files.route('/test-b2')
def test_b2():
    """Full B2 connection test"""
    from app.storage import get_b2_client
    
    b2 = get_b2_client()
    
    if not b2:
        return "<h2>❌ B2 client is None — storage.py issue</h2>"
    
    try:
        bucket = current_app.config['B2_BUCKET']
        result = b2.list_objects_v2(Bucket=bucket)
        count  = result.get('KeyCount', 0)
        return f"""
        <h2>✅ Backblaze B2 Connected!</h2>
        <p>Bucket: <strong>{bucket}</strong></p>
        <p>Files in bucket: <strong>{count}</strong></p>
        <p>Storage: <strong>10 GB Free!</strong></p>
        <br>
        <a href="/dashboard">← Go to Dashboard</a>
        """
    except Exception as e:
        return f"<h2>⚠️ Error:</h2><p>{str(e)}</p>"
    
    
    
@files.route('/test-upload')
@login_required
def test_upload():
    from app.storage import get_b2_client
    b2 = get_b2_client()
    return f"""
    <h2>Upload Test</h2>
    <p>B2 Connected: {'Yes' if b2 else 'No'}</p>
    <p>B2 Bucket: {current_app.config.get('B2_BUCKET')}</p>
    <p>B2 Endpoint: {current_app.config.get('B2_ENDPOINT')}</p>
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Test Upload</button>
    </form>
    """

@files.route('/preview/<int:file_id>')
@login_required
def preview(file_id):
    """Serve file preview"""
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    backend   = getattr(file, 'storage_backend', 'b2') or 'b2'
    file_type = file.file_type.lower()

    image_types = ['jpg','jpeg','png','gif','svg','webp']
    video_types = ['mp4','avi','mov','mkv','webm']
    audio_types = ['mp3','wav','flac','ogg']

    if file_type in image_types:
        # Serve image directly through Flask
        data = download_file(file.stored_name, backend)
        if data:
            from flask import Response
            mime = file.mime_type or f'image/{file_type}'
            return Response(
                data,
                mimetype=mime,
                headers={
                    'Content-Disposition':
                        f'inline; filename="{file.filename}"',
                    'Cache-Control': 'private, max-age=3600',
                }
            )
        return jsonify({'error': 'File not found'}), 404

    elif file_type in video_types:
        url = get_presigned_url(file.stored_name, backend, expires=3600)
        if url:
            return jsonify({'url': url, 'type': file_type})
        return jsonify({'error': 'Could not get video URL'}), 400

    elif file_type in audio_types:
        url = get_presigned_url(file.stored_name, backend, expires=3600)
        if url:
            return jsonify({'url': url, 'type': file_type})
        return jsonify({'error': 'Could not get audio URL'}), 400

    elif file_type == 'pdf':
        url = get_presigned_url(file.stored_name, backend, expires=3600)
        if url:
            return jsonify({'url': url, 'type': 'pdf'})
        return jsonify({'error': 'Could not get PDF URL'}), 400

    else:
        url = get_presigned_url(file.stored_name, backend, expires=3600)
        if url:
            return jsonify({'url': url, 'type': file_type})
        return jsonify({'error': 'Preview not available'}), 400