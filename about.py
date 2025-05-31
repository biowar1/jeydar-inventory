import streamlit as st

def app():
    st.title("ℹ️ About Inventory Management System")
    
    # Main description
    st.markdown("""
    ## 📦 Welcome to the Inventory Management System
    
    This application helps you efficiently manage your inventory with real-time tracking, 
    analytics, and reporting capabilities.
    """)
    

    
    st.markdown("---")
    
   
    
    # User guide
    st.subheader("📖 Quick Start Guide")
    
    with st.expander("🔐 Getting Started"):
        st.markdown("""
        1. **Login** with your credentials or register a new account
        2. **Navigate** using the sidebar menu
        3. **Add items** to your inventory using the Inventory tab
        4. **Monitor** stock levels and generate reports
        5. **Export** data when needed
        """)
    
    with st.expander("📦 Managing Inventory"):
        st.markdown("""
        **Adding Items:**
        - Go to Inventory → Add Item tab
        - Fill in item details (name, category, quantity, price)
        - Click "Add Item" to save
        
        **Updating Items:**
        - Go to Inventory → Update Item tab
        - Select the item you want to modify
        - Update the fields and save changes
        
        **Viewing Inventory:**
        - Use the "View Inventory" tab to see all items
        - Items can be filtered and sorted
        - Delete items if needed
        """)
    
    with st.expander("📊 Reports & Analytics"):
        st.markdown("""
        **Available Reports:**
        - Category distribution analysis
        - Stock level monitoring
        - Value analysis by item and category
        - Low stock alerts
        
        **Exporting Data:**
        - Download inventory as CSV
        - Generate summary reports
        - Custom date range filtering (coming soon)
        """)
    
    with st.expander("👤 Account Management"):
        st.markdown("""
        **User Features:**
        - Update profile information
        - Change password
        - View account details
        
        **Admin Features:**
        - Manage all users
        - Create admin accounts
        - View system statistics
        - Delete users (with confirmation)
        """)
    
    st.markdown("---")
    
    # Support section
    st.subheader("🆘 Support & Help")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Need Help?**
        - Check the user guide above
        - Contact your system administrator
        - Report bugs or issues
        """)
    
    with col2:
        st.markdown("""
        **System Requirements:**
        - Modern web browser
        - Internet connection
        - Valid user account
        """)
    
    # Version info
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>
        Inventory Management System v1.0<br>
        Built with ❤️ using Streamlit and Firebase<br>
        © 2024 - All rights reserved
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    # Debug info for admins
    if st.session_state.get('user', {}).get('role') == 'admin':
        with st.expander("🔧 Debug Information (Admin Only)"):
            st.json({
                "User": st.session_state.get('user', {}),
                "Session State Keys": list(st.session_state.keys()),
                "Authenticated": st.session_state.get('authenticated', False)
            })
