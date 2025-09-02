import streamlit as st
import pandas as pd
from datetime import datetime, date
from psycopg2.extras import RealDictCursor
from utils import (
    format_currency, format_date, format_datetime, create_data_table,
    get_status_color, create_notification_display, create_poll_display
)

class OwnerDashboard:
    def __init__(self, db):
        self.db = db
    
    def show_dashboard(self):
        """Main owner dashboard"""
        user = st.session_state.user
        st.title(f"🏠 Owner Dashboard - Flat {user['flat_number']}")
        
        # Get owner statistics
        stats = self.get_owner_stats(user['flat_number'])
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Pending Bills", stats['pending_bills'])
        
        with col2:
            st.metric("Open Complaints", stats['open_complaints'])
        
        with col3:
            st.metric("Unread Notifications", stats['unread_notifications'])
        
        with col4:
            st.metric("Active Polls", stats['active_polls'])
        
        st.divider()
        
        # Recent activities
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Recent Bills")
            recent_bills = self.get_recent_bills(user['flat_number'], limit=5)
            
            if recent_bills:
                for bill in recent_bills:
                    status_color = get_status_color(bill['payment_status'])
                    st.write(f"{status_color} {bill['bill_type']} - {format_currency(bill['amount'])} (Due: {format_date(bill['due_date'])})")
            else:
                st.info("No recent bills")
        
        with col2:
            st.subheader("📝 Recent Complaints")
            recent_complaints = self.get_recent_complaints(user['user_id'], limit=5)
            
            if recent_complaints:
                for complaint in recent_complaints:
                    status_color = get_status_color(complaint['status'])
                    st.write(f"{status_color} {complaint['title']} - {complaint['status'].title()}")
            else:
                st.info("No recent complaints")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💰 Pay Bills", use_container_width=True):
                st.session_state.selected_tab = "💰 My Bills"
                st.rerun()
        
        with col2:
            if st.button("📝 Raise Complaint", use_container_width=True):
                st.session_state.selected_tab = "📝 My Complaints"
                st.rerun()
        
        with col3:
            if st.button("🗳️ Vote in Polls", use_container_width=True):
                st.session_state.selected_tab = "🗳️ Polls"
                st.rerun()
    
    def get_owner_stats(self, flat_number):
        """Get owner statistics"""
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        stats = {}
        
        # Pending bills
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM bills 
            WHERE flat_number = %s AND payment_status = 'pending'
        """, (flat_number,))
        stats['pending_bills'] = cursor.fetchone()['count']
        
        # Open complaints
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM complaints 
            WHERE flat_number = %s AND status IN ('open', 'in_progress')
        """, (flat_number,))
        stats['open_complaints'] = cursor.fetchone()['count']
        
        # Unread notifications
        user_id = st.session_state.user['user_id']
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM notifications n
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id 
                AND nr.user_id = %s
            WHERE nr.notification_id IS NULL
        """, (user_id,))
        stats['unread_notifications'] = cursor.fetchone()['count']
        
        # Active polls
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM polls 
            WHERE status = 'active'
        """)
        stats['active_polls'] = cursor.fetchone()['count']
        
        cursor.close()
        return stats
    
    def get_recent_bills(self, flat_number, limit=5):
        """Get recent bills for the flat"""
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM bills 
            WHERE flat_number = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (flat_number, limit))
        bills = cursor.fetchall()
        cursor.close()
        return bills
    
    def get_recent_complaints(self, user_id, limit=5):
        """Get recent complaints by the user"""
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM complaints 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (user_id, limit))
        complaints = cursor.fetchall()
        cursor.close()
        return complaints
    
    def show_bills(self):
        """Show bills management"""
        user = st.session_state.user
        st.title("💰 My Bills")
        
        # Check for overdue bills
        from utils import check_overdue_bills
        check_overdue_bills(self.db)
        
        # Get all bills for the flat
        bills = self.db.get_user_bills(user['flat_number'])
        
        if bills:
            # Summary metrics
            total_pending = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'pending')
            total_overdue = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'overdue')
            total_paid = sum(float(bill['amount']) for bill in bills if bill['payment_status'] == 'paid')
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Pending Amount", format_currency(total_pending))
            
            with col2:
                st.metric("Overdue Amount", format_currency(total_overdue))
            
            with col3:
                st.metric("Paid Amount", format_currency(total_paid))
            
            st.divider()
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"])
            with col2:
                bill_type_filter = st.selectbox("Filter by Type", ["all", "Maintenance", "Electricity", "Water", "Parking", "Security", "Other"])
            
            # Apply filters
            filtered_bills = bills
            if status_filter != "all":
                filtered_bills = [bill for bill in filtered_bills if bill['payment_status'] == status_filter]
            if bill_type_filter != "all":
                filtered_bills = [bill for bill in filtered_bills if bill['bill_type'] == bill_type_filter]
            
            # Display bills
            if filtered_bills:
                for bill in filtered_bills:
                    with st.expander(f"{get_status_color(bill['payment_status'])} {bill['bill_type']} - {format_currency(bill['amount'])} (Due: {format_date(bill['due_date'])})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Bill ID:** {bill['bill_id']}")
                            st.write(f"**Type:** {bill['bill_type']}")
                            st.write(f"**Amount:** {format_currency(bill['amount'])}")
                            st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                            st.write(f"**Status:** {bill['payment_status'].title()}")
                            if bill['payment_date']:
                                st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                                st.write(f"**Payment Method:** {bill['payment_method']}")
                        
                        with col2:
                            if bill['payment_status'] in ['pending', 'overdue']:
                                st.subheader("💳 Pay Now")
                                
                                payment_method = st.selectbox(
                                    "Payment Method",
                                    ["Online Banking", "UPI", "Credit Card", "Debit Card", "Cash"],
                                    key=f"payment_method_{bill['bill_id']}"
                                )
                                
                                if st.button("Pay Bill", key=f"pay_{bill['bill_id']}"):
                                    try:
                                        self.db.pay_bill(bill['bill_id'], payment_method)
                                        st.success("Payment successful!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Payment failed: {e}")
            else:
                st.info("No bills found with the selected filters")
        else:
            st.info("No bills found for your flat")
    
    def show_complaints(self):
        """Show complaints management"""
        user = st.session_state.user
        st.title("📝 My Complaints")
        
        tab1, tab2 = st.tabs(["Raise New Complaint", "My Complaints"])
        
        with tab1:
            self.raise_complaint_form()
        
        with tab2:
            self.view_my_complaints()
    
    def raise_complaint_form(self):
        """Raise new complaint form"""
        user = st.session_state.user
        
        st.subheader("➕ Raise New Complaint")
        
        with st.form("raise_complaint_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Complaint Title")
                category = st.selectbox("Category", [
                    "Maintenance",
                    "Plumbing",
                    "Electrical",
                    "Security",
                    "Noise",
                    "Parking",
                    "Cleanliness",
                    "Elevator",
                    "Water Supply",
                    "Other"
                ])
            
            with col2:
                priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"])
            
            description = st.text_area("Description", height=150)
            
            submit = st.form_submit_button("Submit Complaint")
            
            if submit:
                if title and description and category:
                    try:
                        complaint_id = self.db.create_complaint(
                            user['user_id'], 
                            user['flat_number'], 
                            title, 
                            description, 
                            category, 
                            priority
                        )
                        st.success(f"Complaint submitted successfully! Complaint ID: {complaint_id}")
                    except Exception as e:
                        st.error(f"Error submitting complaint: {e}")
                else:
                    st.error("Please fill all required fields")
    
    def view_my_complaints(self):
        """View user's complaints"""
        user = st.session_state.user
        
        complaints = self.db.get_user_complaints(user['user_id'])
        
        if complaints:
            # Filter options
            status_filter = st.selectbox("Filter by Status", ["all", "open", "in_progress", "resolved", "closed"])
            
            # Apply filter
            filtered_complaints = complaints
            if status_filter != "all":
                filtered_complaints = [c for c in complaints if c['status'] == status_filter]
            
            if filtered_complaints:
                for complaint in filtered_complaints:
                    with st.expander(f"{get_status_color(complaint['status'])} #{complaint['complaint_id']} - {complaint['title']} ({complaint['priority'].upper()})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Category:** {complaint['category']}")
                            st.write(f"**Description:** {complaint['description']}")
                            if complaint['admin_response']:
                                st.write(f"**Admin Response:** {complaint['admin_response']}")
                        
                        with col2:
                            st.write(f"**Status:** {complaint['status'].title()}")
                            st.write(f"**Priority:** {complaint['priority'].title()}")
                            st.write(f"**Created:** {format_datetime(complaint['created_at'])}")
                            st.write(f"**Updated:** {format_datetime(complaint['updated_at'])}")
                            if complaint['resolved_at']:
                                st.write(f"**Resolved:** {format_datetime(complaint['resolved_at'])}")
            else:
                st.info("No complaints found with the selected filter")
        else:
            st.info("You haven't raised any complaints yet")
    
    def show_notifications(self):
        """Show notifications"""
        user = st.session_state.user
        st.title("📢 Notifications")
        
        # Get unread notifications
        unread_notifications = self.db.get_unread_notifications(user['user_id'])
        
        if unread_notifications:
            st.subheader("🔴 Unread Notifications")
            create_notification_display(unread_notifications, self.db, user['user_id'])
            st.divider()
        
        # Get all notifications (read and unread)
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT n.*, nr.read_at
            FROM notifications n
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id 
                AND nr.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT 20
        """, (user['user_id'],))
        all_notifications = cursor.fetchall()
        cursor.close()
        
        if all_notifications:
            st.subheader("📜 All Notifications")
            
            for notification in all_notifications:
                read_status = "✅ Read" if notification['read_at'] else "🔴 Unread"
                
                with st.expander(f"{notification['title']} - {read_status} - {format_datetime(notification['created_at'])}"):
                    st.write(notification['message'])
                    if notification['read_at']:
                        st.write(f"*Read on: {format_datetime(notification['read_at'])}*")
                    else:
                        if st.button(f"Mark as Read", key=f"read_all_{notification['notification_id']}"):
                            self.db.mark_notification_read(notification['notification_id'], user['user_id'])
                            st.success("Marked as read!")
                            st.rerun()
        else:
            if not unread_notifications:
                st.info("No notifications")
    
    def show_polls(self):
        """Show polls and voting"""
        user = st.session_state.user
        st.title("🗳️ Polls & Voting")
        
        # Get active polls
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM polls 
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        active_polls = cursor.fetchall()
        
        if active_polls:
            st.subheader("🗳️ Active Polls")
            create_poll_display(active_polls, self.db, user['user_id'])
        
        # Get closed polls with results
        cursor.execute("""
            SELECT * FROM polls 
            WHERE status = 'closed'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        closed_polls = cursor.fetchall()
        
        if closed_polls:
            st.subheader("📊 Recent Poll Results")
            
            for poll in closed_polls:
                with st.expander(f"📊 {poll['title']} (Closed)"):
                    st.write(poll['description'])
                    st.write(f"**End Date:** {format_date(poll['end_date'])}")
                    
                    # Get results
                    cursor.execute("""
                        SELECT option_text, vote_count 
                        FROM poll_options 
                        WHERE poll_id = %s
                        ORDER BY vote_count DESC
                    """, (poll['poll_id'],))
                    
                    results = cursor.fetchall()
                    if results:
                        total_votes = sum(result['vote_count'] for result in results)
                        
                        st.write("**Results:**")
                        for i, result in enumerate(results):
                            percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                            st.write(f"{rank_emoji} {result['option_text']}: {result['vote_count']} votes ({percentage:.1f}%)")
                        
                        st.write(f"**Total Votes:** {total_votes}")
                        
                        # Check if user voted
                        cursor.execute("""
                            SELECT po.option_text 
                            FROM votes v
                            JOIN poll_options po ON v.option_id = po.option_id
                            WHERE v.poll_id = %s AND v.user_id = %s
                        """, (poll['poll_id'], user['user_id']))
                        
                        user_vote = cursor.fetchone()
                        if user_vote:
                            st.info(f"✅ You voted for: {user_vote['option_text']}")
        
        if not active_polls and not closed_polls:
            st.info("No polls available")
        
        cursor.close()
