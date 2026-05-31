# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# ── Database URL setup ──
database_url = os.getenv('DATABASE_URL', 'sqlite:///cloudvault.db')

# Fix postgres:// → postgresql:// (Render/Heroku format)
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Add SSL for Neon if not already there
if 'neon.tech' in database_url and 'sslmode' not in database_url:
    database_url += '?sslmode=require'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

    # ── Database ──
    SQLALCHEMY_DATABASE_URI        = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Add SSL engine options for Neon PostgreSQL
    if 'neon.tech' in database_url:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'sslmode': 'require'
            },
            'pool_pre_ping': True,
            'pool_recycle':  300,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
        }

    # ── Supabase Storage ──
    SUPABASE_URL    = os.getenv('SUPABASE_URL')
    SUPABASE_KEY    = os.getenv('SUPABASE_KEY')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'cloudvault-files')

    # ── Backblaze B2 Storage (10GB free) ──
    B2_KEY_ID   = os.getenv('B2_KEY_ID')
    B2_APP_KEY  = os.getenv('B2_APP_KEY')
    B2_BUCKET   = os.getenv('B2_BUCKET', 'cloudvault-files')
    B2_ENDPOINT = os.getenv('B2_ENDPOINT')

    # ── Storage Limits ──
    STORAGE_LIMIT_GB    = int(os.getenv('STORAGE_LIMIT_GB', 10))
    STORAGE_LIMIT_MB    = int(os.getenv('STORAGE_LIMIT_GB', 10)) * 1024
    STORAGE_LIMIT_BYTES = int(os.getenv('STORAGE_LIMIT_GB', 10)) \
                          * 1024 * 1024 * 1024

    # Max upload size per file — 500MB
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    # ── Flask-Mail (Gmail SMTP) ──
    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USE_SSL        = False
    MAIL_USERNAME       = os.getenv('MAIL_EMAIL')
    MAIL_PASSWORD       = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_EMAIL')

    # ── SendGrid ──
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    MAIL_FROM        = os.getenv('MAIL_FROM')

 