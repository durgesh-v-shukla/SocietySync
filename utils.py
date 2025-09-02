import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
import hashlib

def create_sidebar_navigation(user_role, auth_manager):
    """Create sidebar navigation based on user role"""
    st.sidebar.title("🏢 SocietySync")
    
    user = auth_manager.get_current_user()
    st.sidebar.write(f"Welcome, **{user['name']}**")
    st.sidebar.write(f"Role: **{user_role.title()}**")
    st.sidebar.write(f"Flat: **{user['flat_number']}**")
    
    st.sidebar.divider()
    
    # Navigation options based on role
    if user_role == 'admin':
        options = [
            "🏠 Dashboard",
            "👥 Manage Users",
            "💰 Billing",
            "📝 Complaints",
            "🚶 Visitors",
            "📢 Notifications",
            "🗳️ Polls",
            "👤 Profile"
        ]
    else:  # owner or tenant
        options = [
            "🏠 Dashboard",
            "💰 My Bills",
            "📝 My Complaints",
            "📢 Notifications",
            "🗳️ Polls",
            "👤 Profile"
        ]
    
    selected = st.sidebar.radio("Navigation", options)
    
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Logout"):
        auth_manager.logout()
    
    return selected

def create_pie_chart(data, names, values, title):
    """Create pie chart using Plotly"""
    if data is None or len(data) == 0:
        return None
    
    try:
        df = pd.DataFrame(data)
        if df.empty:
            return None
        
        fig = px.pie(df, names=names, values=values, title=title)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    except Exception as e:
        st.error(f"Error creating pie chart: {e}")
        return None

def create_bar_chart(data, x, y, title):
    """Create bar chart using Plotly"""
    if data is None or len(data) == 0:
        return None
    
    try:
        df = pd.DataFrame(data)
        if df.empty:
            return None
        
        fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(showlegend=False)
        return fig
    except Exception as e:
        st.error(f"Error creating bar chart: {e}")
        return None

def display_notification_badge(unread_count):
    """Display notification badge"""
    if unread_count > 0:
        st.sidebar.error(f"🔴 {unread_count} unread notifications")
    else:
        st.sidebar.success("✅ No unread notifications")

def format_currency(amount):
    """Format currency display"""
    if amount is None:
        return "₹0.00"
    try:
        return f"₹{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

def format_date(date_obj):
    """Format date for display"""
    if date_obj is None:
        return "N/A"
    if isinstance(date_obj, str):
        return date_obj
    try:
        return date_obj.strftime("%d-%m-%Y")
    except AttributeError:
        return "N/A"

def format_datetime(datetime_obj):
    """Format datetime for display"""
    if datetime_obj is None:
        return "N/A"
    if isinstance(datetime_obj, str):
        return datetime_obj
    try:
        return datetime_obj.strftime("%d-%m-%Y %H:%M")
    except AttributeError:
        return "N/A"

def get_status_color(status):
    """Get color for status display"""
    status_colors = {
        'pending': '🟡',
        'paid': '🟢',
        'overdue': '🔴',
        'open': '🟡',
        'in_progress': '🟠',
        'resolved': '🟢',
        'closed': '⚫',
        'active': '🟢',
        'inactive': '🔴'
    }
    return status_colors.get(status.lower(), '⚪')

def create_data_table(data, columns=None):
    """Create formatted data table"""
    if data is None or len(data) == 0:
        st.info("No data available")
        return
        
    try:
        df = pd.DataFrame(data)
        if df.empty:
            st.info("No data available")
            return
        
        # Format specific columns
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: format_currency(x) if x is not None else 'N/A')
        
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].apply(lambda x: format_datetime(x) if x is not None else 'N/A')
        
        if 'due_date' in df.columns:
            df['due_date'] = df['due_date'].apply(lambda x: format_date(x) if x is not None else 'N/A')
        
        if 'payment_date' in df.columns:
            df['payment_date'] = df['payment_date'].apply(lambda x: format_date(x) if x is not None else 'N/A')
        
        if columns:
            st.dataframe(df[columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating data table: {e}")

def validate_email(email):
    """Basic email validation"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone validation"""
    import re
    if not phone:
        return False
    # Remove spaces and special characters
    clean_phone = re.sub(r'[^0-9]', '', phone)
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, clean_phone) is not None

def get_flat_numbers():
    """Get list of flat numbers"""
    # Generate flat numbers (A101, A102, ..., A110, B101, ...)
    flat_numbers = []
    for block in ['A', 'B', 'C', 'D']:
        for floor in range(1, 11):  # 10 floors
            for unit in range(1, 5):  # 4 units per floor
                flat_numbers.append(f"{block}{floor:02d}{unit}")
    return flat_numbers

def check_overdue_bills(db):
    """Check and update overdue bills"""
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            UPDATE bills 
            SET payment_status = 'overdue' 
            WHERE payment_status = 'pending' AND due_date < CURRENT_DATE
        """)
        cursor.close()
    except Exception as e:
        st.error(f"Error checking overdue bills: {e}")

def create_notification_display(notifications, db, user_id):
    """Display notifications with read tracking"""
    if not notifications or len(notifications) == 0:
        st.info("No new notifications")
        return
    
    for notification in notifications:
        with st.expander(f"📢 {notification['title']} - {format_datetime(notification['created_at'])}"):
            st.write(notification['message'])
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"Mark as Read", key=f"read_{notification['notification_id']}"):
                    db.mark_notification_read(notification['notification_id'], user_id)
                    st.success("Marked as read!")
                    st.rerun()

def generate_unique_key(prefix, obj, index=None):
    """
    Generate a unique key for Streamlit elements
    prefix: string prefix for the key
    obj: dictionary containing the data
    index: optional index to ensure uniqueness
    """
    key_parts = [prefix]
    
    # Include unique identifiers from the object
    for field in ['bill_id', 'complaint_id', 'visitor_id', 'notification_id', 'poll_id']:
        if field in obj:
            key_parts.append(str(obj[field]))
            break
    
    # Include additional identifying fields
    for field in ['flat_number', 'bill_type', 'created_at']:
        if field in obj and obj[field]:
            key_parts.append(str(obj[field]).replace(' ', '_'))
    
    # Include index if provided for extra uniqueness
    if index is not None:
        key_parts.append(str(index))
    
    # Include a hash of the object for absolute uniqueness
    obj_str = str(sorted(obj.items()))
    obj_hash = hashlib.md5(obj_str.encode()).hexdigest()[:8]
    key_parts.append(obj_hash)
    
    return "_".join(key_parts)

def create_poll_display(polls, db, user_id):
    """Display polls with voting interface"""
    if not polls or len(polls) == 0:
        st.info("No active polls")
        return
    
    for poll in polls:
        st.subheader(f"🗳️ {poll['title']}")
        st.write(poll['description'])
        
        # Check if user has already voted
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT * FROM votes WHERE poll_id = %s AND user_id = %s
        """, (poll['poll_id'], user_id))
        
        has_voted = cursor.fetchone() is not None
        
        if has_voted:
            st.info("✅ You have already voted in this poll")
            
            # Show results
            cursor.execute("""
                SELECT option_text, vote_count 
                FROM poll_options 
                WHERE poll_id = %s
                ORDER BY vote_count DESC
            """, (poll['poll_id'],))
            
            results = cursor.fetchall()
            if results and len(results) > 0:
                results_df = pd.DataFrame(results, columns=['Option', 'Votes'])
                fig = create_bar_chart(results_df, 'Option', 'Votes', "Poll Results")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            # Show voting options
            cursor.execute("""
                SELECT option_id, option_text 
                FROM poll_options 
                WHERE poll_id = %s
            """, (poll['poll_id'],))
            
            options = cursor.fetchall()
            if options and len(options) > 0:
                option_texts = [opt[1] for opt in options]
                selected_option = st.radio(
                    "Select your choice:",
                    option_texts,
                    key=f"poll_{poll['poll_id']}"
                )
                
                if st.button(f"Vote", key=f"vote_{poll['poll_id']}"):
                    # Find selected option_id
                    selected_option_id = next(opt[0] for opt in options if opt[1] == selected_option)
                    
                    # Record vote
                    cursor.execute("""
                        INSERT INTO votes (poll_id, option_id, user_id)
                        VALUES (%s, %s, %s)
                    """, (poll['poll_id'], selected_option_id, user_id))
                    
                    # Update vote count
                    cursor.execute("""
                        UPDATE poll_options 
                        SET vote_count = vote_count + 1 
                        WHERE option_id = %s
                    """, (selected_option_id,))
                    
                    st.success("Vote recorded successfully!")
                    st.rerun()
        
        cursor.close()
        st.divider()