import streamlit as st
from database import Database

class AuthManager:
    def __init__(self):
        self.db = Database()
    
    def login_form(self):
        """Display login form"""
        st.title("🏢 SocietySync - Smart Apartment ERP")
        st.subheader("Login to your account")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    user = self.db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.success(f"Welcome, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        # Display default admin credentials for demo
        st.info("**Default Admin Login:**\nUsername: admin\nPassword: admin123")
    
    def logout(self):
        """Logout user"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    def check_authentication(self):
        """Check if user is authenticated"""
        return st.session_state.get('logged_in', False)
    
    def get_current_user(self):
        """Get current logged in user"""
        return st.session_state.get('user', None)
    
    def password_change_form(self):
        """Password change form for first-time users"""
        user = self.get_current_user()
        
        if not user['password_changed']:
            st.warning("⚠️ You must change your initial password before proceeding.")
            
            with st.form("password_change_form"):
                st.write(f"Your initial password was: **{user['initial_password']}**")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit = st.form_submit_button("Change Password")
                
                if submit:
                    if new_password and confirm_password:
                        if new_password == confirm_password:
                            if len(new_password) >= 6:
                                self.db.change_password(user['user_id'], new_password)
                                st.success("Password changed successfully!")
                                # Update session
                                st.session_state.user['password_changed'] = True
                                st.rerun()
                            else:
                                st.error("Password must be at least 6 characters long")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please enter both passwords")
            
            return False  # Block access until password is changed
        
        return True  # Allow access
    
    def profile_management(self):
        """Profile management form"""
        user = self.get_current_user()
        
        st.subheader("👤 Profile Management")
        
        with st.form("profile_form"):
            name = st.text_input("Name", value=user['name'])
            email = st.text_input("Email", value=user['email'] or "")
            phone = st.text_input("Phone", value=user['phone'] or "")
            
            # Show flat number but make it read-only
            st.text_input("Flat Number", value=user['flat_number'], disabled=True,
                         help="Flat number cannot be changed")
            
            submit = st.form_submit_button("Update Profile")
            
            if submit:
                try:
                    cursor = self.db.connection.cursor()
                    cursor.execute("""
                        UPDATE users 
                        SET name = %s, email = %s, phone = %s
                        WHERE user_id = %s
                    """, (name, email, phone, user['user_id']))
                    cursor.close()
                    
                    # Update session
                    st.session_state.user['name'] = name
                    st.session_state.user['email'] = email
                    st.session_state.user['phone'] = phone
                    
                    st.success("Profile updated successfully!")
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
        
        # Password change section
        st.subheader("🔒 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            submit_password = st.form_submit_button("Change Password")
            
            if submit_password:
                if current_password and new_password and confirm_new_password:
                    # Verify current password
                    if self.db.authenticate_user(user['username'], current_password):
                        if new_password == confirm_new_password:
                            if len(new_password) >= 6:
                                self.db.change_password(user['user_id'], new_password)
                                st.success("Password changed successfully!")
                            else:
                                st.error("New password must be at least 6 characters long")
                        else:
                            st.error("New passwords do not match")
                    else:
                        st.error("Current password is incorrect")
                else:
                    st.error("Please fill all password fields")
