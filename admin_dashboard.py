import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from psycopg2.extras import RealDictCursor
from utils import (
    create_pie_chart, create_bar_chart, format_currency, 
    format_date, format_datetime, create_data_table,
    validate_email, validate_phone, get_flat_numbers,
    generate_unique_key
)

class AdminDashboard:
    def __init__(self, db):
        self.db = db
    
    def show_dashboard(self):
        """Main admin dashboard"""
        st.title("🏠 Admin Dashboard")
        
        # Get society statistics
        stats = self.db.get_society_stats()
        
        # Display key metrics with clickable buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Owners", stats['total_owners'])
            if st.button("👥 View All Owners", use_container_width=True, key="view_owners_btn"):
                st.session_state.navigate_to = "👥 Manage Users"
                st.session_state.user_tab = "View Users"
                st.session_state.user_filter = "owner"
                st.rerun()
        
        with col2:
            st.metric("Total Tenants", stats['total_tenants'])
            if st.button("🏠 View All Tenants", use_container_width=True, key="view_tenants_btn"):
                st.session_state.navigate_to = "👥 Manage Users"
                st.session_state.user_tab = "View Users"
                st.session_state.user_filter = "tenant"
                st.rerun()
        
        with col3:
            st.metric("Pending Bills", stats['pending_bills'])
            if st.button("💰 View Pending Bills", use_container_width=True, key="view_bills_btn"):
                st.session_state.navigate_to = "💰 Billing"
                st.session_state.bill_tab = "View Bills"
                st.session_state.bill_filter = "pending"
                st.rerun()
        
        with col4:
            st.metric("Open Complaints", stats['open_complaints'])
            if st.button("📝 View Open Complaints", use_container_width=True, key="view_complaints_btn"):
                st.session_state.navigate_to = "📝 Complaints"
                st.session_state.complaint_filter = "open"
                st.rerun()
        
        with col5:
            st.metric("Current Visitors", stats['current_visitors'])
            if st.button("🚶 View Current Visitors", use_container_width=True, key="view_visitors_btn"):
                st.session_state.navigate_to = "🚶 Visitors"
                st.session_state.visitor_filter = "in"
                st.rerun()
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Bill payment statistics - FIXED
            if stats.get('bill_stats') and len(stats['bill_stats']) > 0:
                fig = create_pie_chart(
                    stats['bill_stats'], 
                    'payment_status', 
                    'count', 
                    "Bill Payment Status"
                )
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No bill statistics available")
        
        with col2:
            # Complaint statistics - FIXED
            if stats.get('complaint_stats') and len(stats['complaint_stats']) > 0:
                fig = create_bar_chart(
                    stats['complaint_stats'], 
                    'status', 
                    'count', 
                    "Complaint Status"
                )
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No complaint statistics available")
        
        # Recent activities
        st.subheader("📋 Recent Activities")
        
        # Recent complaints
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.title, c.flat_number, c.priority, c.created_at, u.name
            FROM complaints c
            JOIN users u ON c.user_id = u.user_id
            ORDER BY c.created_at DESC
            LIMIT 5
        """)
        recent_complaints = cursor.fetchall()
        
        if recent_complaints and len(recent_complaints) > 0:
            st.write("**Recent Complaints:**")
            for complaint in recent_complaints:
                st.write(f"• {complaint['title']} - Flat {complaint['flat_number']} ({complaint['name']}) - {format_datetime(complaint['created_at'])}")
        else:
            st.info("No recent complaints")
        
        cursor.close()
        
    def manage_users(self):
        """User management interface"""
        st.title("👥 Manage Users")
        
        # Check for session state tab selection
        default_tab_index = 0
        if hasattr(st.session_state, 'user_tab') and st.session_state.user_tab:
            tab_mapping = {"Add New User": 0, "View Users": 1, "User Details": 2}
            default_tab_index = tab_mapping.get(st.session_state.user_tab, 0)
            st.session_state.user_tab = None
        
        tab1, tab2, tab3 = st.tabs(["Add New User", "View Users", "User Details"])
        
        with tab1:
            self.add_user_form()
        with tab2:
            self.view_users()
        with tab3:
            self.user_details()
    
    def add_user_form(self):
        """Add new user form"""
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                role = st.selectbox("User Role", ["owner", "tenant"], key="user_role_select")
                name = st.text_input("Full Name", key="user_name_input")
                email = st.text_input("Email", key="user_email_input")
                phone = st.text_input("Phone Number", key="user_phone_input")
                flat_number = st.selectbox("Flat Number", get_flat_numbers(), key="user_flat_select")
            
            with col2:
                if role == "owner":
                    ownership_start_date = st.date_input("Ownership Start Date", value=date.today(), key="owner_start_date")
                    emergency_contact = st.text_input("Emergency Contact", key="owner_emergency_contact")
                else:  # tenant
                    # Get available owners for this flat
                    cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("""
                        SELECT o.owner_id, u.name, o.flat_number 
                        FROM owners o 
                        JOIN users u ON o.user_id = u.user_id
                        ORDER BY o.flat_number
                    """)
                    owners = cursor.fetchall()
                    cursor.close()
                    
                    owner_options = {f"{owner['name']} (Flat {owner['flat_number']})": owner['owner_id'] 
                                   for owner in owners}
                    
                    if owner_options:
                        selected_owner = st.selectbox("Owner", list(owner_options.keys()), key="tenant_owner_select")
                        owner_id = owner_options[selected_owner]
                    else:
                        st.error("No owners available. Please add an owner first.")
                        owner_id = None
                    
                    rent_amount = st.number_input("Monthly Rent", min_value=0.0, value=0.0, key="tenant_rent")
                    lease_start_date = st.date_input("Lease Start Date", value=date.today(), key="tenant_lease_start")
                    lease_end_date = st.date_input("Lease End Date", value=date.today() + timedelta(days=365), key="tenant_lease_end")
                    security_deposit = st.number_input("Security Deposit", min_value=0.0, value=0.0, key="tenant_deposit")
            
            submit = st.form_submit_button("Create User", key="create_user_submit")
            
            if submit:
                # Validation
                if not name or not email or not phone:
                    st.error("Please fill all required fields")
                elif not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not validate_phone(phone):
                    st.error("Please enter a valid 10-digit phone number")
                else:
                    try:
                        # Prepare kwargs based on role
                        kwargs = {}
                        if role == "owner":
                            kwargs = {
                                'ownership_start_date': ownership_start_date,
                                'emergency_contact': emergency_contact
                            }
                        else:  # tenant
                            if owner_id is None:
                                st.error("Please select an owner")
                                return
                            
                            kwargs = {
                                'owner_id': owner_id,
                                'rent_amount': rent_amount,
                                'lease_start_date': lease_start_date,
                                'lease_end_date': lease_end_date,
                                'security_deposit': security_deposit
                            }
                        
                        # Create user
                        result = self.db.create_user(role, name, email, phone, flat_number, **kwargs)
                        
                        st.success(f"User created successfully!")
                        st.info(f"**Username:** {result['username']}")
                        st.info(f"**Initial Password:** {result['initial_password']}")
                        st.warning("Please share these credentials with the user. The initial password is also stored in the system for your reference.")
                        
                    except Exception as e:
                        st.error(f"Error creating user: {e}")
    
    def view_users(self):
        """View all users with detailed information"""
        st.subheader("👥 All Users")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            # Check for session state filter
            default_role = "all"
            if hasattr(st.session_state, 'user_filter') and st.session_state.user_filter:
                default_role = st.session_state.user_filter
                st.session_state.user_filter = None
            role_filter = st.selectbox("Filter by Role", ["all", "owner", "tenant"],
                                     index=["all", "owner", "tenant"].index(default_role), key="user_role_filter")
        with col2:
            search_text = st.text_input("Search by Name or Flat", key="user_search_text")
        
        # Get users
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT user_id, username, role, flat_number, name, email, phone, 
                   created_at, last_login, password_changed, initial_password
            FROM users 
            WHERE role != 'admin'
        """
        params = []
        
        if role_filter != "all":
            query += " AND role = %s"
            params.append(role_filter)
        
        if search_text:
            query += " AND (name ILIKE %s OR flat_number ILIKE %s)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        cursor.close()
        
        if users and len(users) > 0:
            # Display users in a table format
            users_data = []
            for user in users:
                users_data.append({
                    'Name': user['name'],
                    'Role': user['role'].title(),
                    'Flat': user['flat_number'],
                    'Email': user['email'],
                    'Phone': user['phone'],
                    'Username': user['username'],
                    'Password Changed': '✅' if user['password_changed'] else '❌',
                    'Last Login': format_datetime(user['last_login']),
                    'Created': format_datetime(user['created_at'])
                })
            
            df = pd.DataFrame(users_data)
            st.dataframe(df, use_container_width=True)
            
            # Show initial passwords for users who haven't changed them
            st.subheader("🔑 Initial Passwords (Not Changed)")
            unchanged_users = [user for user in users if not user['password_changed']]
            
            if unchanged_users:
                for user in unchanged_users:
                    st.write(f"**{user['name']}** ({user['username']}): `{user['initial_password']}`")
            else:
                st.info("All users have changed their initial passwords.")
        else:
            st.info("No users found")
    
    def user_details(self):
        """View detailed user information"""
        st.subheader("👤 User Details")
        
        # User selection
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT user_id, name, username, flat_number 
            FROM users 
            WHERE role != 'admin'
            ORDER BY name
        """)
        users = cursor.fetchall()
        
        if users and len(users) > 0:
            user_options = {f"{user['name']} ({user['flat_number']})": user['user_id'] for user in users}
            selected_user = st.selectbox("Select User", list(user_options.keys()), key="user_details_select")
            user_id = user_options[selected_user]
            
            # Get user details
            cursor.execute("""
                SELECT * FROM users WHERE user_id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if user:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Name: {user['name']}")
                    st.write(f"Role: {user['role'].title()}")
                    st.write(f"Flat Number: {user['flat_number']}")
                    st.write(f"Email: {user['email']}")
                    st.write(f"Phone: {user['phone']}")
                    st.write(f"Username: {user['username']}")
                
                with col2:
                    st.write("**Account Information**")
                    st.write(f"Created: {format_datetime(user['created_at'])}")
                    st.write(f"Last Login: {format_datetime(user['last_login'])}")
                    st.write(f"Password Changed: {'Yes' if user['password_changed'] else 'No'}")
                    if not user['password_changed']:
                        st.write(f"Initial Password: `{user['initial_password']}`")
                
                # Role-specific information
                if user['role'] == 'owner':
                    cursor.execute("""
                        SELECT * FROM owners WHERE user_id = %s
                    """, (user_id,))
                    owner_info = cursor.fetchone()
                    
                    if owner_info:
                        st.write("**Owner Information**")
                        st.write(f"Ownership Start Date: {format_date(owner_info['ownership_start_date'])}")
                        st.write(f"Emergency Contact: {owner_info['emergency_contact']}")
                
                elif user['role'] == 'tenant':
                    cursor.execute("""
                        SELECT t.*, u.name as owner_name 
                        FROM tenants t
                        LEFT JOIN owners o ON t.owner_id = o.owner_id
                        LEFT JOIN users u ON o.user_id = u.user_id
                        WHERE t.user_id = %s
                    """, (user_id,))
                    tenant_info = cursor.fetchone()
                    
                    if tenant_info:
                        st.write("**Tenant Information**")
                        st.write(f"Owner: {tenant_info['owner_name']}")
                        st.write(f"Monthly Rent: {format_currency(tenant_info['rent_amount'])}")
                        st.write(f"Lease Start: {format_date(tenant_info['lease_start_date'])}")
                        st.write(f"Lease End: {format_date(tenant_info['lease_end_date'])}")
                        st.write(f"Security Deposit: {format_currency(tenant_info['security_deposit'])}")
        
        cursor.close()
    
    def billing_management(self):
        """Billing management interface"""
        st.title("💰 Billing Management")
        
        # Check for session state tab selection
        default_tab_index = 0
        if hasattr(st.session_state, 'bill_tab') and st.session_state.bill_tab:
            tab_mapping = {"Create Bills": 0, "View Bills": 1, "Payment Tracking": 2}
            default_tab_index = tab_mapping.get(st.session_state.bill_tab, 0)
            st.session_state.bill_tab = None
        
        tab1, tab2, tab3 = st.tabs(["Create Bills", "View Bills", "Payment Tracking"])
        
        with tab1:
            self.create_bill_form()
        with tab2:
            self.view_bills()
        with tab3:
            self.payment_tracking()
    
    def create_bill_form(self):
        """Create new bill form"""
        st.subheader("📄 Create New Bill")
        
        with st.form("create_bill_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                flat_number = st.selectbox("Flat Number", get_flat_numbers(), key="bill_flat_select")
                bill_type = st.selectbox("Bill Type", [
                    "Maintenance",
                    "Electricity",
                    "Water",
                    "Parking",
                    "Security",
                    "Other"
                ], key="bill_type_select")
                amount = st.number_input("Amount", min_value=0.0, value=0.0, key="bill_amount_input")
            
            with col2:
                due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30), key="bill_due_date")
                description = st.text_area("Description (Optional)", key="bill_description")
            
            submit = st.form_submit_button("Create Bill", key="create_bill_submit")
            
            if submit:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute("""
                            INSERT INTO bills (flat_number, bill_type, amount, due_date, created_by)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING bill_id
                        """, (flat_number, bill_type, amount, due_date, st.session_state.user['user_id']))
                        
                        bill_id = cursor.fetchone()[0]
                        cursor.close()
                        
                        st.success(f"Bill created successfully! Bill ID: {bill_id}")
                        
                    except Exception as e:
                        st.error(f"Error creating bill: {e}")
    
    def view_bills(self):
        """View all bills with detailed user information"""
        st.subheader("📋 All Bills")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            # Check for session state filter
            default_status = "all"
            if hasattr(st.session_state, 'bill_filter') and st.session_state.bill_filter:
                default_status = st.session_state.bill_filter
                st.session_state.bill_filter = None
            status_filter = st.selectbox("Filter by Status", ["all", "pending", "paid", "overdue"], 
                                       index=["all", "pending", "paid", "overdue"].index(default_status), key="bill_status_filter")
        with col2:
            bill_type_filter = st.selectbox("Filter by Type", ["all", "Maintenance", "Electricity", "Water", "Parking", "Security", "Other"], key="bill_type_filter")
        with col3:
            flat_filter = st.text_input("Filter by Flat Number", key="bill_flat_filter")
        
        # Get bills with user information
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT b.*, u.name as resident_name, u.role as resident_type
            FROM bills b
            LEFT JOIN users u ON b.flat_number = u.flat_number
            WHERE 1=1
        """
        params = []
        
        if status_filter != "all":
            query += " AND b.payment_status = %s"
            params.append(status_filter)
        
        if bill_type_filter != "all":
            query += " AND b.bill_type = %s"
            params.append(bill_type_filter)
        
        if flat_filter:
            query += " AND b.flat_number ILIKE %s"
            params.append(f"%{flat_filter}%")
        
        query += " ORDER BY b.created_at DESC"
        
        cursor.execute(query, params)
        bills = cursor.fetchall()
        cursor.close()
        
        # Check for and remove duplicates
        unique_bills = []
        seen_bill_ids = set()
        for bill in bills:
            if bill['bill_id'] not in seen_bill_ids:
                unique_bills.append(bill)
                seen_bill_ids.add(bill['bill_id'])
        
        if len(bills) != len(unique_bills):
            st.warning(f"Filtered out {len(bills) - len(unique_bills)} duplicate bills")
            bills = unique_bills
        
        if bills and len(bills) > 0:
            st.write(f"**Found {len(bills)} bills**")
            
            # Display bills with detailed information
            for i, bill in enumerate(bills):
                status_color = "🟡" if bill['payment_status'] == 'pending' else ("🟢" if bill['payment_status'] == 'paid' else "🔴")
                resident_info = f"{bill['resident_name']} ({bill['resident_type'].title()})" if bill['resident_name'] else "No Resident"
                
                with st.expander(f"{status_color} #{bill['bill_id']} - {bill['bill_type']} - {format_currency(bill['amount'])} - Flat {bill['flat_number']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Resident:** {resident_info}")
                        st.write(f"**Flat Number:** {bill['flat_number']}")
                        st.write(f"**Bill Type:** {bill['bill_type']}")
                        st.write(f"**Amount:** {format_currency(bill['amount'])}")
                        st.write(f"**Due Date:** {format_date(bill['due_date'])}")
                        st.write(f"**Created:** {format_datetime(bill['created_at'])}")
                        
                        if bill['payment_date']:
                            st.write(f"**Payment Date:** {format_date(bill['payment_date'])}")
                            st.write(f"**Payment Method:** {bill['payment_method']}")
                    
                    with col2:
                        st.write(f"**Status:** {bill['payment_status'].title()}")
                        
                        if bill['payment_status'] == 'pending':
                            st.warning("⏳ Payment Pending")
                        elif bill['payment_status'] == 'overdue':
                            st.error("🚨 Overdue!")
                        else:
                            st.success("✅ Paid")
                        
                        # Admin actions for pending bills
                        if bill['payment_status'] in ['pending', 'overdue']:
                            # Create a truly unique key
                            unique_key = generate_unique_key("mark_paid", bill, i)
                            
                            if st.button("Mark as Paid", key=unique_key):
                                try:
                                    cursor = self.db.connection.cursor()
                                    cursor.execute("""
                                        UPDATE bills 
                                        SET payment_status = 'paid', payment_date = CURRENT_DATE, 
                                            payment_method = 'Admin Override'
                                        WHERE bill_id = %s
                                    """, (bill['bill_id'],))
                                    cursor.close()
                                    st.success("Bill marked as paid!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

        else:
            st.info("No bills found with the selected filters")
    
    def payment_tracking(self):
        """Payment tracking and analytics"""
        st.subheader("📊 Payment Analytics")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        # Payment statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bills,
                COUNT(CASE WHEN payment_status = 'paid' THEN 1 END) as paid_bills,
                COUNT(CASE WHEN payment_status = 'pending' THEN 1 END) as pending_bills,
                COUNT(CASE WHEN payment_status = 'overdue' THEN 1 END) as overdue_bills,
                SUM(amount) as total_amount,
                SUM(CASE WHEN payment_status = 'paid' THEN amount ELSE 0 END) as collected_amount
            FROM bills
        """)
        
        stats = cursor.fetchone()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bills", stats['total_bills'] or 0)
            st.metric("Paid Bills", stats['paid_bills'] or 0)
        
        with col2:
            st.metric("Pending Bills", stats['pending_bills'] or 0)
            st.metric("Overdue Bills", stats['overdue_bills'] or 0)
        
        with col3:
            st.metric("Total Amount", format_currency(stats['total_amount'] or 0))
        
        with col4:
            st.metric("Collected Amount", format_currency(stats['collected_amount'] or 0))
            collection_rate = (stats['collected_amount'] or 0) / (stats['total_amount'] or 1) * 100
            st.metric("Collection Rate", f"{collection_rate:.1f}%")
        
        cursor.close()
    
    def complaint_management(self):
        """Complaint management interface"""
        st.title("📝 Complaint Management")
        
        tab1, tab2 = st.tabs(["All Complaints", "Complaint Analytics"])
        
        with tab1:
            self.view_all_complaints()
        with tab2:
            self.complaint_analytics()
    
    def view_all_complaints(self):
        """View and manage all complaints"""
        st.subheader("📋 All Complaints")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            # Check for session state filter
            default_status = "all"
            if hasattr(st.session_state, 'complaint_filter') and st.session_state.complaint_filter:
                default_status = st.session_state.complaint_filter
                st.session_state.complaint_filter = None
            status_filter = st.selectbox("Filter by Status", ["all", "open", "in_progress", "resolved", "closed"],
                                       index=["all", "open", "in_progress", "resolved", "closed"].index(default_status), key="complaint_status_filter")
        with col2:
            priority_filter = st.selectbox("Filter by Priority", ["all", "low", "medium", "high", "urgent"], key="complaint_priority_filter")
        with col3:
            flat_filter = st.text_input("Filter by Flat", key="complaint_flat_filter")
        
        # Get complaints
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT c.*, u.name as user_name 
            FROM complaints c
            JOIN users u ON c.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if status_filter != "all":
            query += " AND c.status = %s"
            params.append(status_filter)
        
        if priority_filter != "all":
            query += " AND c.priority = %s"
            params.append(priority_filter)
        
        if flat_filter:
            query += " AND c.flat_number ILIKE %s"
            params.append(f"%{flat_filter}%")
        
        query += " ORDER BY c.created_at DESC"
        
        cursor.execute(query, params)
        complaints = cursor.fetchall()
        
        if complaints and len(complaints) > 0:
            for complaint in complaints:
                with st.expander(f"#{complaint['complaint_id']} - {complaint['title']} ({complaint['priority'].upper()})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Complainant:** {complaint['user_name']}")
                        st.write(f"**Flat:** {complaint['flat_number']}")
                        st.write(f"**Category:** {complaint['category']}")
                        st.write(f"**Description:** {complaint['description']}")
                        if complaint['admin_response']:
                            st.write(f"**Admin Response:** {complaint['admin_response']}")
                    
                    with col2:
                        st.write(f"**Status:** {complaint['status'].title()}")
                        st.write(f"**Priority:** {complaint['priority'].title()}")
                        st.write(f"**Created:** {format_datetime(complaint['created_at'])}")
                        if complaint['resolved_at']:
                            st.write(f"**Resolved:** {format_datetime(complaint['resolved_at'])}")
                    
                    # Admin actions
                    st.subheader("Admin Actions")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_status = st.selectbox(
                            "Update Status",
                            ["open", "in_progress", "resolved", "closed"],
                            index=["open", "in_progress", "resolved", "closed"].index(complaint['status']),
                            key=f"status_{complaint['complaint_id']}"
                        )
                    
                    with col2:
                        if st.button("Update Status", key=f"update_{complaint['complaint_id']}"):
                            cursor.execute("""
                                UPDATE complaints 
                                SET status = %s, updated_at = CURRENT_TIMESTAMP,
                                    resolved_at = CASE WHEN %s = 'resolved' THEN CURRENT_TIMESTAMP ELSE resolved_at END
                                WHERE complaint_id = %s
                            """, (new_status, new_status, complaint['complaint_id']))
                            st.success("Status updated!")
                            st.rerun()
                    
                    # Admin response
                    admin_response = st.text_area(
                        "Admin Response",
                        value=complaint['admin_response'] or "",
                        key=f"response_{complaint['complaint_id']}"
                    )
                    
                    if st.button("Save Response", key=f"save_response_{complaint['complaint_id']}"):
                        cursor.execute("""
                            UPDATE complaints 
                            SET admin_response = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE complaint_id = %s
                        """, (admin_response, complaint['complaint_id']))
                        st.success("Response saved!")
                        st.rerun()
        else:
            st.info("No complaints found")
        
        cursor.close()
    
    def complaint_analytics(self):
        """Complaint analytics"""
        st.subheader("📊 Complaint Analytics")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        # Complaint statistics
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM complaints
            GROUP BY status
        """)
        status_stats = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                priority,
                COUNT(*) as count
            FROM complaints
            GROUP BY priority
        """)
        priority_stats = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as count
            FROM complaints
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        category_stats = cursor.fetchall()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # FIXED: Check length instead of truthiness
            if status_stats and len(status_stats) > 0:
                fig = create_pie_chart(status_stats, 'status', 'count', "Complaints by Status")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status statistics available")
        
        with col2:
            # FIXED: Check length instead of truthiness
            if priority_stats and len(priority_stats) > 0:
                fig = create_bar_chart(priority_stats, 'priority', 'count', "Complaints by Priority")
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No priority statistics available")
        
        # FIXED: Check length instead of truthiness
        if category_stats and len(category_stats) > 0:
            fig = create_bar_chart(category_stats, 'category', 'count', "Top Complaint Categories")
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category statistics available")
        
        cursor.close()
    
    def visitor_management(self):
        """Visitor management interface"""
        st.title("🚶 Visitor Management")
        
        tab1, tab2, tab3 = st.tabs(["Log Visitor", "Current Visitors", "Visitor History"])
        
        with tab1:
            self.log_visitor_form()
        with tab2:
            self.current_visitors()
        with tab3:
            self.visitor_history()
    
    def log_visitor_form(self):
        """Log new visitor form"""
        st.subheader("➕ Log New Visitor")
        
        with st.form("log_visitor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                flat_number = st.selectbox("Visiting Flat", get_flat_numbers(), key="visitor_flat_select")
                visitor_name = st.text_input("Visitor Name", key="visitor_name_input")
                visitor_phone = st.text_input("Visitor Phone", key="visitor_phone_input")
            
            with col2:
                purpose = st.text_input("Purpose of Visit", key="visitor_purpose_input")
                vehicle_number = st.text_input("Vehicle Number (Optional)", key="visitor_vehicle_input")
            
            submit = st.form_submit_button("Log Visitor", key="log_visitor_submit")
            
            if submit:
                if visitor_name and flat_number:
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute("""
                            INSERT INTO visitors (flat_number, visitor_name, visitor_phone, purpose, 
                                                vehicle_number, logged_by)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING visitor_id
                        """, (flat_number, visitor_name, visitor_phone, purpose, vehicle_number,
                              st.session_state.user['user_id']))
                        
                        visitor_id = cursor.fetchone()[0]
                        cursor.close()
                        
                        st.success(f"Visitor logged successfully! Visitor ID: {visitor_id}")
                        
                    except Exception as e:
                        st.error(f"Error logging visitor: {e}")
                else:
                    st.error("Please enter visitor name and select flat number")
    
    def current_visitors(self):
        """View current visitors"""
        st.subheader("👥 Current Visitors")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM visitors 
            WHERE status = 'in'
            ORDER BY entry_time DESC
        """)
        current_visitors = cursor.fetchall()
        
        if current_visitors and len(current_visitors) > 0:
            for visitor in current_visitors:
                with st.expander(f"{visitor['visitor_name']} - Flat {visitor['flat_number']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Name:** {visitor['visitor_name']}")
                        st.write(f"**Phone:** {visitor['visitor_phone']}")
                        st.write(f"**Purpose:** {visitor['purpose']}")
                        st.write(f"**Vehicle:** {visitor['vehicle_number']}")
                        st.write(f"**Entry Time:** {format_datetime(visitor['entry_time'])}")
                    
                    with col2:
                        if st.button("Mark Exit", key=f"exit_{visitor['visitor_id']}"):
                            cursor.execute("""
                                UPDATE visitors 
                                SET status = 'out', exit_time = CURRENT_TIMESTAMP
                                WHERE visitor_id = %s
                            """, (visitor['visitor_id'],))
                            st.success("Visitor marked as exited!")
                            st.rerun()
        else:
            st.info("No current visitors")
        
        cursor.close()

    def visitor_history(self):
        """View visitor history"""
        st.subheader("📜 Visitor History")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            flat_filter = st.text_input("Filter by Flat", key="visitor_history_flat_filter")
        with col2:
            date_filter = st.date_input("Filter by Date", value=None, key="visitor_history_date_filter")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM visitors WHERE 1=1"
        params = []
        
        # Handle flat filter
        if flat_filter and flat_filter.strip():
            query += " AND flat_number ILIKE %s"
            params.append(f"%{flat_filter.strip()}%")
        
        # Handle date filter - more robust version
        try:
            if (date_filter is not None and 
                hasattr(date_filter, 'strftime') and  # Check if it's a date-like object
                not pd.isnull(date_filter)):  # Check if it's not a pandas null
                
                query += " AND DATE(entry_time) = %s"
                params.append(date_filter)
        except (AttributeError, TypeError):
            # If date_filter is not a proper date object, skip the filter
            pass
        
        query += " ORDER BY entry_time DESC LIMIT 100"
        
        try:
            cursor.execute(query, params)
            visitors = cursor.fetchall()
            
            if visitors and len(visitors) > 0:
                visitors_data = []
                for visitor in visitors:
                    visitors_data.append({
                        'Name': visitor['visitor_name'],
                        'Flat': visitor['flat_number'],
                        'Phone': visitor['visitor_phone'],
                        'Purpose': visitor['purpose'],
                        'Vehicle': visitor['vehicle_number'],
                        'Entry Time': format_datetime(visitor['entry_time']),
                        'Exit Time': format_datetime(visitor['exit_time']) if visitor['exit_time'] else 'Still In',
                        'Status': visitor['status'].title()
                    })
                
                df = pd.DataFrame(visitors_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No visitor records found")
        
        except Exception as e:
            st.error(f"Error fetching visitor history: {e}")
        
        finally:
            cursor.close()
    

    
    def notification_management(self):
        """Notification management interface"""
        st.title("📢 Notification Management")
        
        tab1, tab2 = st.tabs(["Send Notification", "Notification History"])
        
        with tab1:
            self.send_notification_form()
        with tab2:
            self.notification_history()
    
    def send_notification_form(self):
        """Send notification form"""
        st.subheader("📤 Send New Notification")
        
        with st.form("send_notification_form"):
            title = st.text_input("Notification Title", key="notification_title_input")
            message = st.text_area("Message", height=150, key="notification_message_input")
            priority = st.selectbox("Priority", ["low", "normal", "high"], key="notification_priority_select")
            
            submit = st.form_submit_button("Send Notification", key="send_notification_submit")
            
            if submit:
                if title and message:
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute("""
                                                        INSERT INTO notifications (title, message, created_by, priority)
                            VALUES (%s, %s, %s, %s)
                            RETURNING notification_id
                        """, (title, message, st.session_state.user['user_id'], priority))
                        
                        notification_id = cursor.fetchone()[0]
                        cursor.close()
                        
                        st.success(f"Notification sent successfully! Notification ID: {notification_id}")
                        
                    except Exception as e:
                        st.error(f"Error sending notification: {e}")
                else:
                    st.error("Please enter title and message")
    
    def notification_history(self):
        """View notification history"""
        st.subheader("📜 Notification History")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT n.*, u.name as created_by_name,
                   COUNT(nr.notification_id) as read_count
            FROM notifications n
            JOIN users u ON n.created_by = u.user_id
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id
            GROUP BY n.notification_id, u.name
            ORDER BY n.created_at DESC
        """)
        notifications = cursor.fetchall()
        
        if notifications and len(notifications) > 0:
            for notification in notifications:
                with st.expander(f"{notification['title']} - {format_datetime(notification['created_at'])}"):
                    st.write(f"**Message:** {notification['message']}")
                    st.write(f"**Priority:** {notification['priority'].title()}")
                    st.write(f"**Created by:** {notification['created_by_name']}")
                    st.write(f"**Read by:** {notification['read_count']} users")
        else:
            st.info("No notifications found")
        
        cursor.close()
    
    def poll_management(self):
        """Poll management interface"""
        st.title("🗳️ Poll Management")
        
        tab1, tab2, tab3 = st.tabs(["Create Poll", "Active Polls", "Poll Results"])
        
        with tab1:
            self.create_poll_form()
        with tab2:
            self.active_polls()
        with tab3:
            self.poll_results()
    
    def create_poll_form(self):
        """Create poll form"""
        st.subheader("➕ Create New Poll")
        
        with st.form("create_poll_form"):
            title = st.text_input("Poll Title", key="poll_title_input")
            description = st.text_area("Poll Description", key="poll_description_input")
            end_date = st.date_input("End Date", value=date.today() + timedelta(days=7), key="poll_end_date")
            
            st.write("**Poll Options** (Enter each option on a new line)")
            options_text = st.text_area("Options", height=150, 
                                       placeholder="Option 1\nOption 2\nOption 3",
                                       key="poll_options_input")
            
            submit = st.form_submit_button("Create Poll", key="create_poll_submit")
            
            if submit:
                if title and options_text:
                    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                    
                    if len(options) >= 2:
                        try:
                            cursor = self.db.connection.cursor()
                            
                            # Create poll
                            cursor.execute("""
                                INSERT INTO polls (title, description, created_by, end_date)
                                VALUES (%s, %s, %s, %s)
                                RETURNING poll_id
                            """, (title, description, st.session_state.user['user_id'], end_date))
                            
                            poll_id = cursor.fetchone()[0]
                            
                            # Create poll options
                            for option in options:
                                cursor.execute("""
                                    INSERT INTO poll_options (poll_id, option_text)
                                    VALUES (%s, %s)
                                """, (poll_id, option))
                            
                            cursor.close()
                            
                            st.success(f"Poll created successfully! Poll ID: {poll_id}")
                            
                        except Exception as e:
                            st.error(f"Error creating poll: {e}")
                    else:
                        st.error("Please provide at least 2 options")
                else:
                    st.error("Please enter poll title and options")
    
    def active_polls(self):
        """View active polls"""
        st.subheader("🗳️ Active Polls")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.*, u.name as created_by_name
            FROM polls p
            JOIN users u ON p.created_by = u.user_id
            WHERE p.status = 'active'
            ORDER BY p.created_at DESC
        """)
        polls = cursor.fetchall()
        
        if polls and len(polls) > 0:
            for poll in polls:
                with st.expander(f"{poll['title']} (Ends: {format_date(poll['end_date'])})"):
                    st.write(f"**Description:** {poll['description']}")
                    st.write(f"**Created by:** {poll['created_by_name']}")
                    st.write(f"**Created:** {format_datetime(poll['created_at'])}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Close Poll", key=f"close_{poll['poll_id']}"):
                            cursor.execute("""
                                UPDATE polls SET status = 'closed' WHERE poll_id = %s
                            """, (poll['poll_id'],))
                            st.success("Poll closed!")
                            st.rerun()
                    
                    with col2:
                        # Show current vote count
                        cursor.execute("""
                            SELECT COUNT(*) as vote_count 
                            FROM votes 
                            WHERE poll_id = %s
                        """, (poll['poll_id'],))
                        vote_count = cursor.fetchone()['vote_count']
                        st.write(f"**Total Votes:** {vote_count}")
        else:
            st.info("No active polls")
        
        cursor.close()
    
    def poll_results(self):
        """View poll results"""
        st.subheader("📊 Poll Results")
        
        cursor = self.db.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM polls 
            ORDER BY created_at DESC
        """)
        polls = cursor.fetchall()
        
        # FIXED: Check length instead of truthiness
        if polls and len(polls) > 0:
            for poll in polls:
                st.write(f"### {poll['title']}")
                st.write(f"**Status:** {poll['status'].title()}")
                st.write(f"**End Date:** {format_date(poll['end_date'])}")
                
                # Get poll results
                cursor.execute("""
                    SELECT option_text, vote_count 
                    FROM poll_options 
                    WHERE poll_id = %s
                    ORDER BY vote_count DESC
                """, (poll['poll_id'],))
                
                results = cursor.fetchall()
                
                # FIXED: Check length instead of truthiness
                if results and len(results) > 0:
                    total_votes = sum(result['vote_count'] for result in results)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write("**Results:**")
                        for i, result in enumerate(results):
                            percentage = (result['vote_count'] / total_votes * 100) if total_votes > 0 else 0
                            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else "•"
                            st.write(f"{rank_emoji} {result['option_text']}: {result['vote_count']} votes ({percentage:.1f}%)")
                        
                        st.write(f"**Total Votes:** {total_votes}")
                    
                    with col2:
                        # FIXED: Check length and total_votes explicitly
                        if len(results) > 0 and total_votes > 0:
                            results_df = pd.DataFrame(results)
                            fig = create_bar_chart(results_df, 'option_text', 'vote_count', f"Results: {poll['title']}")
                            if fig is not None:
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No votes yet")
                
                st.divider()
        else:
            st.info("No polls found")
        
        cursor.close()