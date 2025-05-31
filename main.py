import streamlit as st
from streamlit_option_menu import option_menu
import os
import home, inventory, reports, account, about, login
from PIL import Image
from firebase_config import initialize_firebase

# Set page configuration as the first command
st.set_page_config(
    page_title="Inventory Management System",
    page_icon="📦",
    layout="wide"
)

# Initialize Firebase
initialize_firebase()

class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        # Check if user is authenticated
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user' not in st.session_state:
            st.session_state.user = None

        # If not authenticated, show login page
        if not st.session_state.authenticated:
            user = login.login_page()
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()
            return

        # User is authenticated, show the main app
        user = st.session_state.user
        
        # Initialize logout confirmation state
        if 'show_logout_confirmation' not in st.session_state:
            st.session_state.show_logout_confirmation = False

        # Handle page redirects from quick actions
        if 'page_redirect' in st.session_state:
            redirect_page = st.session_state.page_redirect
            del st.session_state.page_redirect
            
            # Map redirect to menu options
            redirect_map = {
                "inventory": "Inventory",
                "reports": "Reports", 
                "account": "Account"
            }
            
            if redirect_page in redirect_map:
                st.session_state.selected_page = redirect_map[redirect_page]

        with st.sidebar:
            # Add logo at the top of sidebar
            st.markdown("# 📦 Inventory System")
            
            # Check if user is admin
            if user.get('role') == 'admin':
                app = option_menu(
                    menu_title='Admin Panel',
                    options=['Home', 'Inventory', 'Reports', 'Account', 'About'],
                    icons=['house-fill', 'box-seam', 'graph-up', 'person-circle', 'info-circle-fill'],
                    menu_icon='gear-fill',
                    default_index=0,
                    key='admin_menu',
                    styles={
                        "container": {"padding": "5!important", "background-color": '#1f1f1f'},
                        "icon": {"color": "white", "font-size": "23px"},
                        "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px", "--hover-color": "#02ab21"},
                        "nav-link-selected": {"background-color": "#02ab21"},
                    }
                )
                
                st.markdown("---")
                st.success("🛡️ Welcome Admin!")
            else:
                app = option_menu(
                    menu_title='Inventory System',
                    options=['Home', 'Inventory', 'Reports', 'Account', 'About'],
                    icons=['house-fill', 'box-seam', 'graph-up', 'person-circle', 'info-circle-fill'],
                    menu_icon='box-seam',
                    default_index=0,
                    key='user_menu',
                    styles={
                        "container": {"padding": "5!important", "background-color": '#1f1f1f'},
                        "icon": {"color": "white", "font-size": "23px"},
                        "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px", "--hover-color": "#02ab21"},
                        "nav-link-selected": {"background-color": "#02ab21"},
                    }
                )
                st.success(f"👤 Welcome, {user.get('username', 'User')}!")

            # Add some spacing
            st.markdown("<br>" * 2, unsafe_allow_html=True)

            # Logout confirmation logic
            if not st.session_state.show_logout_confirmation:
                if st.button("🚪 Logout", type="secondary", use_container_width=True):
                    st.session_state.show_logout_confirmation = True
                    st.rerun()
            else:
                st.warning("⚠️ Are you sure you want to logout?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes", type="primary", use_container_width=True):
                        # Clear all session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", type="secondary", use_container_width=True):
                        st.session_state.show_logout_confirmation = False
                        st.rerun()

        # Override app selection if there's a redirect
        if 'selected_page' in st.session_state:
            app = st.session_state.selected_page
            del st.session_state.selected_page

        # Page navigation based on selected option
        if app == "Home":
            home.app()
        elif app == "Inventory":
            inventory.app()
        elif app == "Reports":
            reports.app()
        elif app == "Account":
            account.app()
        elif app == "About":
            about.app()

# Run the application
if __name__ == "__main__":
    MultiApp().run()
