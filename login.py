import streamlit as st
from firebase_config import (
    authenticate_user,
    create_pending_user,
    check_username_exists,
    check_email_exists
)

def login_page():
    """Display login page and handle authentication"""
    
    st.markdown("# 🔐 Login to Inventory System")
    
    # Initialize session state for page navigation
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'
    
    # Show appropriate form based on current page
    if st.session_state.auth_page == 'login':
        user = show_login_form()
        if user:  # If user successfully logged in
            return user
    elif st.session_state.auth_page == 'register':
        show_register_form()
    
    return None  # Return None if no successful login

def show_login_form():
    """Show the main login form"""
    st.markdown("### Please enter your credentials")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            submit_button = st.form_submit_button("🔑 Login", type="primary", use_container_width=True)
        
        if submit_button:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    # Check if user account is approved
                    if user.get('status') == 'pending':
                        st.warning("⏳ Your account is pending admin approval. Please wait for approval.")
                        return None
                    elif user.get('status') == 'rejected':
                        st.error("❌ Your account has been rejected. Please contact the administrator.")
                        return None
                    elif user.get('status') == 'approved' or user.get('role') == 'admin':
                        st.success("Login successful!")
                        # Reset auth page
                        st.session_state.auth_page = 'login'
                        return user
                    else:
                        st.error("❌ Account status unknown. Please contact the administrator.")
                        return None
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.error("❌ Please enter both username and password")
    
    # Register link
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 Create New Account", use_container_width=True):
            st.session_state.auth_page = 'register'
            st.rerun()
    
    return None

def show_register_form():
    """Show the registration form"""
    st.markdown("### 📝 Create New Account")
    st.info("Your account will need admin approval before you can login.")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*", placeholder="Enter username")
            email = st.text_input("Email*", placeholder="your-email@example.com")
        
        with col2:
            full_name = st.text_input("Full Name*", placeholder="Enter your full name")
            department = st.text_input("Department", placeholder="Your department (optional)")
        
        password = st.text_input("Password*", type="password", placeholder="Enter password (min 6 characters)")
        confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
        
        # Additional info
        reason = st.text_area("Reason for Access", placeholder="Why do you need access to the inventory system?")
        
        col1, col2 = st.columns(2)
        with col1:
            register_button = st.form_submit_button("📝 Register", type="primary", use_container_width=True)
        with col2:
            back_button = st.form_submit_button("⬅️ Back to Login", use_container_width=True)
        
        if register_button:
            # Validation
            if not all([username, email, full_name, password, confirm_password]):
                st.error("❌ Please fill in all required fields (marked with *)")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            if password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            # Check if username or email already exists
            if check_username_exists(username):
                st.error("❌ Username already exists. Please choose a different one.")
                return
            
            if check_email_exists(email):
                st.error("❌ Email already registered. Please use a different email.")
                return
            
            # Create pending user account
            user_data = {
                'username': username,
                'email': email,
                'full_name': full_name,
                'department': department,
                'password': password,
                'reason': reason,
                'role': 'user',
                'status': 'pending'
            }
            
            if create_pending_user(user_data):
                st.success("✅ Account created successfully! Your account is pending admin approval. You will be notified once approved.")
                st.info("💡 Please contact your administrator if you need urgent access.")
                # Reset form
                st.session_state.auth_page = 'login'
                st.rerun()
            else:
                st.error("❌ Failed to create account. Please try again.")
        
        if back_button:
            st.session_state.auth_page = 'login'
            st.rerun()
