# -*- coding: utf-8 -*-
# app/storage.py
# Handles Backblaze B2 storage (S3-compatible)
# Free 10GB — no card needed!

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from flask import current_app
import io


def get_b2_client():
    key_id   = current_app.config.get('B2_KEY_ID')
    app_key  = current_app.config.get('B2_APP_KEY')
    endpoint = current_app.config.get('B2_ENDPOINT')

    print(f"DEBUG B2 - key_id: '{key_id}'")
    print(f"DEBUG B2 - endpoint: '{endpoint}'")

    if not key_id or not app_key or not endpoint:
        print("DEBUG B2 - Missing values!")
        return None

    try:
        client = boto3.client(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key,
            config=BotoConfig(signature_version='s3v4')
        )
        print("DEBUG B2 - Client created successfully!")
        return client
    except Exception as e:
        print(f"DEBUG B2 - Client error: {e}")
        return None


def get_supabase_client():
    """Get Supabase client as fallback"""
    try:
        from supabase import create_client
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_KEY')
        if not url or not key or 'your_supabase' in str(url):
            return None
        return create_client(url, key)
    except Exception:
        return None


def upload_file(file_content, stored_name, mime_type):
    """
    Upload file — tries B2 first, then Supabase, then local.
    Returns which backend was used: 'b2', 'supabase', or 'local'
    """
    # ── Try Backblaze B2 ──
    b2 = get_b2_client()
    if b2:
        try:
            bucket = current_app.config['B2_BUCKET']
            b2.put_object(
                Bucket=bucket,
                Key=stored_name,
                Body=file_content,
                ContentType=mime_type
            )
            print(f"✅ Uploaded to B2: {stored_name}")
            return 'b2'
        except Exception as e:
            print(f"❌ B2 upload error: {e}")

    # ── Try Supabase ──
    supabase = get_supabase_client()
    if supabase:
        try:
            bucket = current_app.config['SUPABASE_BUCKET']
            supabase.storage.from_(bucket).upload(
                path=stored_name,
                file=file_content,
                file_options={"content-type": mime_type}
            )
            print(f"✅ Uploaded to Supabase: {stored_name}")
            return 'supabase'
        except Exception as e:
            print(f"❌ Supabase upload error: {e}")

    # ── Local fallback ──
    print("⚠️ Using local storage fallback")
    return 'local'


def download_file(stored_name, storage_backend='b2'):
    """
    Download file as bytes.
    Returns bytes or None if failed.
    """
    # ── Try B2 ──
    if storage_backend in ('b2', 'r2'):
        b2 = get_b2_client()
        if b2:
            try:
                bucket = current_app.config['B2_BUCKET']
                response = b2.get_object(Bucket=bucket, Key=stored_name)
                data = response['Body'].read()
                print(f"✅ Downloaded from B2: {stored_name}")
                return data
            except Exception as e:
                print(f"❌ B2 download error: {e}")

    # ── Try Supabase ──
    supabase = get_supabase_client()
    if supabase:
        try:
            bucket = current_app.config['SUPABASE_BUCKET']
            data = supabase.storage.from_(bucket).download(stored_name)
            print(f"✅ Downloaded from Supabase: {stored_name}")
            return data
        except Exception as e:
            print(f"❌ Supabase download error: {e}")

    return None


def delete_file(stored_name, storage_backend='b2'):
    """Delete file from storage. Returns True if successful."""

    # ── Try B2 ──
    if storage_backend in ('b2', 'r2'):
        b2 = get_b2_client()
        if b2:
            try:
                bucket = current_app.config['B2_BUCKET']
                b2.delete_object(Bucket=bucket, Key=stored_name)
                print(f"✅ Deleted from B2: {stored_name}")
                return True
            except Exception as e:
                print(f"❌ B2 delete error: {e}")

    # ── Try Supabase ──
    supabase = get_supabase_client()
    if supabase:
        try:
            bucket = current_app.config['SUPABASE_BUCKET']
            supabase.storage.from_(bucket).remove([stored_name])
            print(f"✅ Deleted from Supabase: {stored_name}")
            return True
        except Exception as e:
            print(f"❌ Supabase delete error: {e}")

    return False


def get_presigned_url(stored_name, storage_backend='b2', expires=3600):
    """
    Generate a temporary download URL.
    Works for both B2 and Supabase.
    """
    # ── B2 Presigned URL ──
    if storage_backend in ('b2', 'r2'):
        b2 = get_b2_client()
        if b2:
            try:
                bucket = current_app.config['B2_BUCKET']
                url = b2.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': bucket,
                        'Key': stored_name
                    },
                    ExpiresIn=expires
                )
                print(f"✅ B2 presigned URL generated")
                return url
            except Exception as e:
                print(f"❌ B2 presigned URL error: {e}")

    # ── Supabase Signed URL ──
    supabase = get_supabase_client()
    if supabase:
        try:
            bucket = current_app.config['SUPABASE_BUCKET']
            response = supabase.storage.from_(bucket).create_signed_url(
                stored_name, expires
            )
            if isinstance(response, dict):
                url = (response.get('signedURL') or
                       response.get('signedUrl') or
                       response.get('signed_url'))
                if url:
                    return url
        except Exception as e:
            print(f"❌ Supabase signed URL error: {e}")

    return None