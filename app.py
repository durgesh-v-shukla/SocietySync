import streamlit as st
import os
from database import Database
from auth import AuthManager
from admin_dashboard import AdminDashboard
from owner_dashboard import OwnerDashboard
from tenant_dashboard import TenantDashboard
from utils import create_sidebar_navigation, display_notification_badge


# Page configuration
st.set_page_config(
    page_title="SocietySync - Smart Apartment ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = None


# In app.py - improve the main() function
def main():
    """Main application function"""
    try:
        # Initialize database and auth manager
        db = Database()
        
        # Test connection immediately
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            st.error("❌ Database connection failed. Please check your database server.")
            st.error(f"Error details: {str(e)}")
            
            # Show connection help
            with st.expander("Connection Help"):
                st.write("""
                1. Make sure PostgreSQL is running
                2. Check your DATABASE_URL environment variable
                3. Verify the database 'societysync' exists
                4. Ensure username/password are correct
                """)
            
            if st.button("🔄 Try Again"):
                st.rerun()
            return
        
        auth_manager = AuthManager()
        
        # Rest of your main function...
        
        # Show loading spinner while checking authentication
        with st.spinner("Checking authentication..."):
            authenticated = auth_manager.check_authentication()
        
        if not authenticated:
            # Show login form
            auth_manager.login_form()
        else:
            # User is logged in
            user = auth_manager.get_current_user()
            
            # Check if password needs to be changed
            if not auth_manager.password_change_form():
                return  # Block access until password is changed
            
            # Get user role
            user_role = user['role']
            
            # Create sidebar navigation with notification badge
            unread_notifications = db.get_unread_notifications(user['user_id'])
            display_notification_badge(len(unread_notifications))
            
            selected = create_sidebar_navigation(user_role, auth_manager)
            
            # Override with session state if available
            if st.session_state.selected_tab:
                selected = st.session_state.selected_tab
                st.session_state.selected_tab = None
            
            # Handle navigation from dashboard clicks
            if hasattr(st.session_state, 'navigate_to') and st.session_state.navigate_to:
                selected = st.session_state.navigate_to
                st.session_state.navigate_to = None
            
            # Route to appropriate dashboard based on role
            if user_role == 'admin':
                admin_dashboard = AdminDashboard(db)
                handle_admin_navigation(admin_dashboard, selected, auth_manager)
            
            elif user_role == 'owner':
                owner_dashboard = OwnerDashboard(db)
                handle_owner_navigation(owner_dashboard, selected, auth_manager)
            
            elif user_role == 'tenant':
                tenant_dashboard = TenantDashboard(db)
                handle_tenant_navigation(tenant_dashboard, selected, auth_manager)
    
    except Exception as e:
        st.error(f"Application Error: {e}")
        st.error("Please check your database connection and try again.")
        print(f"Error: {e}")  # Log error to console for debugging
        
        # Fallback login form
        if st.button("Try Again"):
            st.experimental_rerun()


def handle_admin_navigation(admin_dashboard, selected, auth_manager):
    """Handle admin dashboard navigation"""
    if selected == "🏠 Dashboard":
        admin_dashboard.show_dashboard()
    
    elif selected == "👥 Manage Users":
        admin_dashboard.manage_users()
    
    elif selected == "💰 Billing":
        admin_dashboard.billing_management()
    
    elif selected == "📝 Complaints":
        admin_dashboard.complaint_management()
    
    elif selected == "🚶 Visitors":
        admin_dashboard.visitor_management()
    
    elif selected == "📢 Notifications":
        admin_dashboard.notification_management()
    
    elif selected == "🗳️ Polls":
        admin_dashboard.poll_management()
    
    elif selected == "👤 Profile":
        auth_manager.profile_management()


def handle_owner_navigation(owner_dashboard, selected, auth_manager):
    """Handle owner dashboard navigation"""
    if selected == "🏠 Dashboard":
        owner_dashboard.show_dashboard()
    
    elif selected == "💰 My Bills":
        owner_dashboard.show_bills()
    
    elif selected == "📝 My Complaints":
        owner_dashboard.show_complaints()
    
    elif selected == "📢 Notifications":
        owner_dashboard.show_notifications()
    
    elif selected == "🗳️ Polls":
        owner_dashboard.show_polls()
    
    elif selected == "👤 Profile":
        auth_manager.profile_management()


def handle_tenant_navigation(tenant_dashboard, selected, auth_manager):
    """Handle tenant dashboard navigation"""
    if selected == "🏠 Dashboard":
        tenant_dashboard.show_dashboard()
    
    elif selected == "💰 My Bills":
        tenant_dashboard.show_bills()
    
    elif selected == "📝 My Complaints":
        tenant_dashboard.show_complaints()
    
    elif selected == "📢 Notifications":
        tenant_dashboard.show_notifications()
    
    elif selected == "🗳️ Polls":
        tenant_dashboard.show_polls()
    
    elif selected == "👤 Profile":
        auth_manager.profile_management()


if __name__ == "__main__":
    main()
