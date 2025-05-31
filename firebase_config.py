import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import hashlib
from datetime import datetime, timedelta

def initialize_firebase():
    """Initialize Firebase connection"""
    if not firebase_admin._apps:
        try:
            # Try to get credentials from Streamlit secrets (for deployment)
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                # Convert secrets to dict for credentials
                firebase_secrets = {
                    "type": st.secrets["firebase"]["type"],
                    "project_id": st.secrets["firebase"]["project_id"],
                    "private_key_id": st.secrets["firebase"]["private_key_id"],
                    "private_key": st.secrets["firebase"]["private_key"],
                    "client_email": st.secrets["firebase"]["client_email"],
                    "client_id": st.secrets["firebase"]["client_id"],
                    "auth_uri": st.secrets["firebase"]["auth_uri"],
                    "token_uri": st.secrets["firebase"]["token_uri"],
                    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
                }
                cred = credentials.Certificate(firebase_secrets)
            else:
                # Use local credentials file for development
                cred = credentials.Certificate('firebase-credentials.json')
            
            firebase_admin.initialize_app(cred)
            return True  # Return True on success
        except Exception as e:
            st.error(f"Error initializing Firebase: {e}")
            return False
    return True  # Already initialized

def get_db():
    """Get Firestore database instance"""
    if initialize_firebase():
        return firestore.client()
    return None


def authenticate_user(username, password):
    """Authenticate user against Firestore"""
    db = get_db()
    if not db:
        return None
    
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).where('password', '==', password)
        docs = query.stream()
        
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            return user_data
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

        return None

def find_user_by_email(email):
    """Find user by email address"""
    db = get_db()
    if not db:
        return None
    
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email)
        docs = query.stream()
        
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            return user_data
        return None
    except Exception as e:
        st.error(f"Error finding user: {e}")
        return None

def generate_reset_code():
    """Generate a 6-digit reset code"""
    return ''.join(random.choices(string.digits, k=6))

def send_reset_email(email, username, reset_code):
    """Send reset code via email using Gmail SMTP"""
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets.get("email", {}).get("sender_email", "")
        sender_password = st.secrets.get("email", {}).get("app_password", "")
        
        if not sender_email or not sender_password:
            st.error("Email configuration not found in secrets")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Code - Inventory System"
        message["From"] = sender_email
        message["To"] = email
        
        # Create HTML content
        html = f"""
        <html>
          <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2 style="color: #333;">Password Reset Request</h2>
              <p>Hello <strong>{username}</strong>,</p>
              <p>You requested a password reset for your Inventory System account.</p>
              <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p>Your reset code is:</p>
                <h1 style="font-size: 32px; color: #02ab21; letter-spacing: 5px; margin: 10px 0;">{reset_code}</h1>
              </div>
              <p><strong>This code will expire in 15 minutes.</strong></p>
              <p>If you didn't request this reset, please ignore this email.</p>
              <hr style="margin: 30px 0;">
              <p style="color: #666;">Best regards,<br>Inventory System Team</p>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

def store_reset_code(user_id, reset_code):
    """Store reset code in Firestore with expiration"""
    db = get_db()
    if not db:
        return False
    
    try:
        # Calculate expiration time (15 minutes from now)
        expiration = datetime.now() + timedelta(minutes=15)
        
        reset_data = {
            'user_id': user_id,
            'reset_code': reset_code,
            'created_at': firestore.SERVER_TIMESTAMP,
            'expires_at': expiration,
            'used': False
        }
        
        db.collection('password_resets').add(reset_data)
        return True
    except Exception as e:
        st.error(f"Error storing reset code: {e}")
        return False

def verify_reset_code(email, reset_code):
    """Verify reset code and return user if valid"""
    db = get_db()
    if not db:
        return None
    
    try:
        # Find user by email
        user = find_user_by_email(email)
        if not user:
            return None
        
        # Find valid reset code
        resets_ref = db.collection('password_resets')
        query = resets_ref.where('user_id', '==', user['id']).where('reset_code', '==', reset_code).where('used', '==', False)
        docs = query.stream()
        
        for doc in docs:
            reset_data = doc.to_dict()
            # Check if code hasn't expired
            if reset_data['expires_at'] > datetime.now():
                # Mark code as used
                doc.reference.update({'used': True})
                return user
        
        return None
    except Exception as e:
        st.error(f"Error verifying reset code: {e}")
        return None

def update_user_password(user_id, new_password):
    """Update user password in Firestore"""
    db = get_db()
    if not db:
        return False
    
    try:
        db.collection('users').document(user_id).update({
            'password': new_password,
            'password_updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        st.error(f"Error updating password: {e}")
        return False

# Additional helper functions for better security

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash"""
    return hash_password(password) == hashed_password
# Add these functions to your existing firebase_config.py

def create_pending_user(user_data):
    """Create a new user with pending status"""
    db = get_db()
    if not db:
        return False
    
    try:
        # Add timestamp
        user_data['created_at'] = firestore.SERVER_TIMESTAMP
        user_data['last_updated'] = firestore.SERVER_TIMESTAMP
        
        # Add user to Firestore
        db.collection('users').add(user_data)
        return True
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def check_username_exists(username):
    """Check if username already exists"""
    db = get_db()
    if not db:
        return False
    
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username)
        docs = list(query.stream())
        return len(docs) > 0
    except Exception as e:
        st.error(f"Error checking username: {e}")
        return False

def check_email_exists(email):
    """Check if email already exists"""
    db = get_db()
    if not db:
        return False
    
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email)
        docs = list(query.stream())
        return len(docs) > 0
    except Exception as e:
        st.error(f"Error checking email: {e}")
        return False

def get_pending_users():
    """Get all users with pending status"""
    db = get_db()
    if not db:
        return []
    
    try:
        users_ref = db.collection('users')
        query = users_ref.where('status', '==', 'pending')
        docs = query.stream()
        
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            users.append(user_data)
        
        return users
    except Exception as e:
        st.error(f"Error getting pending users: {e}")
        return []

def approve_user(user_id):
    """Approve a pending user"""
    db = get_db()
    if not db:
        return False
    
    try:
        db.collection('users').document(user_id).update({
            'status': 'approved',
            'approved_at': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        st.error(f"Error approving user: {e}")
        return False

def reject_user(user_id):
    """Reject a pending user"""
    db = get_db()
    if not db:
        return False
    
    try:
        db.collection('users').document(user_id).update({
            'status': 'rejected',
            'rejected_at': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        st.error(f"Error rejecting user: {e}")
        return False

def cleanup_expired_reset_codes():
    """Clean up expired reset codes from database"""
    db = get_db()
    if not db:
        return False
    
    try:
        resets_ref = db.collection('password_resets')
        expired_query = resets_ref.where('expires_at', '<', datetime.now())
        expired_docs = expired_query.stream()
        
        for doc in expired_docs:
            doc.reference.delete()
        
        return True
    except Exception as e:
        st.error(f"Error cleaning up expired codes: {e}")
        return False
