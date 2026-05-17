# app/models.py
# Models = Database Tables
# Each class here = one table in our SQLite database

from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# This function tells Flask-Login how to find a user by their ID
# It's required for the login system to work
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    This is the 'users' table in our database.
    UserMixin adds helpful methods like is_authenticated, is_active, etc.
    db.Model means this class IS a database table.
    """
    __tablename__ = 'users'
    
    # Each line below is a COLUMN in the users table
    id = db.Column(db.Integer, primary_key=True)          # Auto ID: 1, 2, 3...
    username = db.Column(db.String(80), unique=True, nullable=False)  # Must be unique
    email = db.Column(db.String(120), unique=True, nullable=False)    # Must be unique
    password_hash = db.Column(db.String(256), nullable=False)         # Hashed password
    profile_pic = db.Column(db.String(256), default='default.png')   # Profile picture
    created_at = db.Column(db.DateTime, default=datetime.utcnow)      # Join date
    storage_used = db.Column(db.Float, default=0.0)                   # Bytes used
    
    # This creates a relationship: one user HAS MANY files
    # 'backref' lets us do file.owner to get the user who owns a file
    files = db.relationship('File', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        # This is just for debugging - shows something useful when you print a User object
        return f'<User {self.username}>'


class File(db.Model):
    """
    This is the 'files' table in our database.
    Every uploaded file gets a row here.
    """
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)          # Original file name
    stored_name = db.Column(db.String(256), nullable=False)       # Name we save it as in Supabase
    file_size = db.Column(db.Float, nullable=False, default=0)    # Size in bytes
    file_type = db.Column(db.String(50), nullable=False)          # e.g., 'pdf', 'jpg'
    mime_type = db.Column(db.String(100))                         # e.g., 'application/pdf'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow) # Upload time
    
    # Share settings
    is_shared = db.Column(db.Boolean, default=False)              # Is the file shared publicly?
    share_token = db.Column(db.String(64), unique=True)           # Unique link token
    
    # Foreign key: connects each file to a user
    # This means "this file belongs to the user with this ID"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<File {self.filename}>'
    
    def get_size_display(self):
        """Convert bytes to human-readable format like '2.5 MB'"""
        size = self.file_size
        if size < 1024:
            return f"{size:.0f} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.1f} GB"
    
    def get_icon(self):
        """Return an icon emoji based on file type"""
        icons = {
            'pdf': '📄', 'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊', 'csv': '📊',
            'ppt': '📋', 'pptx': '📋',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️', 'webp': '🖼️',
            'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'mkv': '🎬',
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦',
            'py': '🐍', 'js': '⚡', 'html': '🌐', 'css': '🎨',
            'txt': '📃', 'md': '📃',
        }
        return icons.get(self.file_type.lower(), '📁')