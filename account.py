import streamlit as st
from firebase_config import (
    get_db, 
    get_pending_users, 
    approve_user, 
    reject_user
)
from firebase_admin import firestore
import pandas as pd

def app():
    st.title("👤 Account Settings")
    
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("User not logged in")
        return
    
    user = st.session_state.user
    db = get_db()
    
    if not db:
        st.error("Database connection failed")
        return
    
    # User profile section
    st.subheader("📋 Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Username:** {user.get('username', 'N/A')}")
        st.info(f"**Email:** {user.get('email', 'N/A')}")
    
    with col2:
        st.info(f"**Role:** {user.get('role', 'user').title()}")
        st.info(f"**Status:** {user.get('status', 'approved').title()}")
    
    st.markdown("---")
    
    # Update profile
    st.subheader("✏️ Update Profile")
    
    with st.form("update_profile"):
        new_email = st.text_input("Email", value=user.get('email', ''))
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Profile"):
            if new_email:
                try:
                    update_data = {
                        'email': new_email,
                        'last_updated': firestore.SERVER_TIMESTAMP
                    }
                    
                    if new_password:
                        if new_password == confirm_password:
                            update_data['password'] = new_password
                        else:
                            st.error("Passwords do not match!")
                            return
                    
                    db.collection('users').document(user['id']).update(update_data)
                    st.success("Profile updated successfully!")
                    
                    # Update session state
                    st.session_state.user.update(update_data)
                    
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
            else:
                st.error("Email is required!")
    
    st.markdown("---")
    
    # Admin functions
    if user.get('role') == 'admin':
        st.subheader("🔧 Admin Functions")
        
        tab1, tab2, tab3 = st.tabs(["Pending Approvals", "User Management", "System Stats"])
        
        with tab1:
            st.write("**Pending User Approvals:**")
            
            pending_users = get_pending_users()
            
            if pending_users:
                for pending_user in pending_users:
                    with st.expander(f"👤 {pending_user.get('full_name', 'N/A')} (@{pending_user.get('username', 'N/A')})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Email:** {pending_user.get('email', 'N/A')}")
                            st.write(f"**Department:** {pending_user.get('department', 'N/A')}")
                            st.write(f"**Created:** {pending_user.get('created_at', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Username:** {pending_user.get('username', 'N/A')}")
                            st.write(f"**Reason:** {pending_user.get('reason', 'No reason provided')}")
                        
                        col1, col2, col3 = st.columns([1, 1, 2])
                        
                        with col1:
                            if st.button(f"✅ Approve", key=f"approve_{pending_user['id']}"):
                                if approve_user(pending_user['id']):
                                    st.success("User approved!")
                                    st.rerun()
                                else:
                                    st.error("Failed to approve user")
                        
                        with col2:
                            if st.button(f"❌ Reject", key=f"reject_{pending_user['id']}"):
                                if reject_user(pending_user['id']):
                                    st.success("User rejected!")
                                    st.rerun()
                                else:
                                    st.error("Failed to reject user")
            else:
                st.info("No pending user approvals")
        
        with tab2:
            st.write("**All Users:**")
            try:
                users = []
                docs = db.collection('users').stream()
                
                for doc in docs:
                    user_data = doc.to_dict()
                    user_data['id'] = doc.id
                    users.append({
                        'Username': user_data.get('username'),
                        'Full Name': user_data.get('full_name', 'N/A'),
                        'Email': user_data.get('email'),
                        'Role': user_data.get('role'),
                        'Status': user_data.get('status', 'approved'),
                        'ID': user_data['id']
                    })
                
                if users:
                    df = pd.DataFrame(users)
                    st.dataframe(df, use_container_width=True)
                    
                    # Delete user functionality
                    st.subheader("Delete User")
                    user_to_delete = st.selectbox(
                        "Select user to delete:",
                        [""] + [f"{u['Username']} ({u['Email']})" for u in users if u['ID'] != user['id']]
                    )
                    
                    if user_to_delete and st.button("🗑️ Delete User", type="secondary"):
                        if st.checkbox("I confirm I want to delete this user"):
                            try:
                                # Extract user ID from selection
                                selected_user = next(u for u in users if f"{u['Username']} ({u['Email']})" == user_to_delete)
                                db.collection('users').document(selected_user['ID']).delete()
                                st.success("User deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting user: {e}")
                    
                    # Create new admin user
                    st.subheader("Create Admin User")
                    with st.form("create_admin"):
                        admin_username = st.text_input("Admin Username")
                        admin_email = st.text_input("Admin Email")
                        admin_password = st.text_input("Admin Password", type="password")
                        admin_full_name = st.text_input("Admin Full Name")
                        
                        if st.form_submit_button("Create Admin"):
                            if admin_username and admin_email and admin_password and admin_full_name:
                                try:
                                    # Check if username or email already exists
                                    from firebase_config import check_username_exists, check_email_exists
                                    
                                    if check_username_exists(admin_username):
                                        st.error("Username already exists!")
                                        return
                                    
                                    if check_email_exists(admin_email):
                                        st.error("Email already exists!")
                                        return
                                    
                                    # Create admin user directly (no approval needed)
                                    admin_data = {
                                        'username': admin_username,
                                        'email': admin_email,
                                        'full_name': admin_full_name,
                                        'password': admin_password,
                                        'role': 'admin',
                                        'status': 'approved',
                                        'created_at': firestore.SERVER_TIMESTAMP,
                                        'created_by': user['id']
                                    }
                                    
                                    db.collection('users').add(admin_data)
                                    st.success("Admin user created successfully!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error creating admin: {e}")
                            else:
                                st.error("Please fill all fields")
                
            except Exception as e:
                st.error(f"Error loading users: {e}")
        
        with tab3:
            st.write("**System Statistics:**")
            try:
                # Get inventory stats
                inventory_docs = list(db.collection('inventory').stream())
                user_docs = list(db.collection('users').stream())
                pending_users = get_pending_users()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Users", len(user_docs))
                
                with col2:
                    st.metric("Pending Approvals", len(pending_users))
                
                with col3:
                    st.metric("Total Inventory Items", len(inventory_docs))
                
                with col4:
                    admin_count = sum(1 for doc in user_docs if doc.to_dict().get('role') == 'admin')
                    st.metric("Admin Users", admin_count)
                
                # User status breakdown
                st.subheader("User Status Breakdown")
                status_counts = {}
                for doc in user_docs:
                    status = doc.to_dict().get('status', 'approved')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Approved Users", status_counts.get('approved', 0))
                with col2:
                    st.metric("Pending Users", status_counts.get('pending', 0))
                with col3:
                    st.metric("Rejected Users", status_counts.get('rejected', 0))
                
                # Recent registrations
                st.subheader("Recent Registrations")
                try:
                    recent_users = []
                    for doc in user_docs:
                        user_data = doc.to_dict()
                        if 'created_at' in user_data:
                            recent_users.append({
                                'Username': user_data.get('username'),
                                'Full Name': user_data.get('full_name', 'N/A'),
                                'Status': user_data.get('status', 'approved'),
                                'Created': user_data.get('created_at', 'N/A')
                            })
                    
                    # Sort by creation date (most recent first)
                    # Note: This is a simplified sort, you might want to implement proper date sorting
                    recent_users = recent_users[-10:]  # Show last 10 users
                    
                    if recent_users:
                        df_recent = pd.DataFrame(recent_users)
                        st.dataframe(df_recent, use_container_width=True)
                    else:
                        st.info("No recent registrations")
                        
                except Exception as e:
                    st.error(f"Error loading recent registrations: {e}")
                
            except Exception as e:
                st.error(f"Error loading system stats: {e}")
