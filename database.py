import psycopg2
import os
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import datetime, date
import secrets
import string


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            # Connect using DATABASE_URL environment variable
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is not set")
            
            self.connection = psycopg2.connect(db_url)
            self.connection.autocommit = True
            self.create_tables()
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables with proper relationships"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'owner', 'tenant')),
                flat_number VARCHAR(10),
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(15),
                profile_picture TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_changed BOOLEAN DEFAULT FALSE,
                initial_password VARCHAR(50)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                owner_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                flat_number VARCHAR(10) NOT NULL,
                ownership_start_date DATE,
                emergency_contact VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                owner_id INTEGER REFERENCES owners(owner_id),
                flat_number VARCHAR(10) NOT NULL,
                rent_amount DECIMAL(10,2),
                lease_start_date DATE,
                lease_end_date DATE,
                security_deposit DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_id SERIAL PRIMARY KEY,
                flat_number VARCHAR(10) NOT NULL,
                bill_type VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                due_date DATE NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'overdue')),
                payment_date DATE,
                payment_method VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                flat_number VARCHAR(10) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
                admin_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                visitor_id SERIAL PRIMARY KEY,
                flat_number VARCHAR(10) NOT NULL,
                visitor_name VARCHAR(100) NOT NULL,
                visitor_phone VARCHAR(15),
                purpose VARCHAR(200),
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP,
                vehicle_number VARCHAR(20),
                logged_by INTEGER REFERENCES users(user_id),
                status VARCHAR(20) DEFAULT 'in' CHECK (status IN ('in', 'out'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_reads (
                read_id SERIAL PRIMARY KEY,
                notification_id INTEGER REFERENCES notifications(notification_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(notification_id, user_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                poll_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                created_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date DATE,
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS poll_options (
                option_id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES polls(poll_id) ON DELETE CASCADE,
                option_text VARCHAR(200) NOT NULL,
                vote_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                vote_id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES polls(poll_id) ON DELETE CASCADE,
                option_id INTEGER REFERENCES poll_options(option_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(poll_id, user_id)
            )
        """)
        
        self.create_default_admin()
        cursor.close()
    
    def create_default_admin(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1")
        if cursor.fetchone():
            cursor.close()
            return
        
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, name, email, flat_number)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("admin", password_hash, "admin", "System Administrator", "admin@societysync.com", "ADMIN"))
        
        cursor.close()
    
    def generate_username(self, role, name):
        base_username = f"{role}_{name.lower().replace(' ', '_')}"
        cursor = self.connection.cursor()
        
        counter = 1
        username = base_username
        while True:
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                break
            username = f"{base_username}_{counter}"
            counter += 1
        
        cursor.close()
        return username
    
    def generate_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def authenticate_user(self, username, password):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT user_id, username, password_hash, role, flat_number, name, email, phone, 
                   password_changed, initial_password
            FROM users WHERE username = %s
        """, (username,))
        
        user = cursor.fetchone()
        cursor.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            self.update_last_login(user['user_id'])
            return dict(user)
        
        return None
    
    def update_last_login(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s
        """, (user_id,))
        cursor.close()
    
    def change_password(self, user_id, new_password):
        cursor = self.connection.cursor()
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            UPDATE users SET password_hash = %s, password_changed = TRUE 
            WHERE user_id = %s
        """, (password_hash, user_id))
        
        cursor.close()
        return True
    
    def create_user(self, role, name, email, phone, flat_number, **kwargs):
        cursor = self.connection.cursor()
        
        username = self.generate_username(role, name)
        initial_password = self.generate_password()
        password_hash = bcrypt.hashpw(initial_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, flat_number, name, email, phone, initial_password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id
        """, (username, password_hash, role, flat_number, name, email, phone, initial_password))
        
        user_id = cursor.fetchone()[0]
        
        if role == 'owner':
            cursor.execute("""
                INSERT INTO owners (user_id, flat_number, ownership_start_date, emergency_contact)
                VALUES (%s, %s, %s, %s)
            """, (user_id, flat_number, kwargs.get('ownership_start_date'), kwargs.get('emergency_contact')))
        
        elif role == 'tenant':
            cursor.execute("""
                INSERT INTO tenants (user_id, flat_number, rent_amount, lease_start_date, 
                                     lease_end_date, security_deposit, owner_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, flat_number, kwargs.get('rent_amount'), kwargs.get('lease_start_date'),
                  kwargs.get('lease_end_date'), kwargs.get('security_deposit'), kwargs.get('owner_id')))
        
        cursor.close()
        return {'username': username, 'initial_password': initial_password, 'user_id': user_id}
    
    def get_society_stats(self):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'owner'")
        stats['total_owners'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'tenant'")
        stats['total_tenants'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM bills WHERE payment_status = 'pending'")
        stats['pending_bills'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE status IN ('open', 'in_progress')")
        stats['open_complaints'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE status = 'in'")
        stats['current_visitors'] = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT payment_status, COUNT(*) as count 
            FROM bills 
            GROUP BY payment_status
        """)
        stats['bill_stats'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM complaints 
            GROUP BY status
        """)
        stats['complaint_stats'] = cursor.fetchall()
        
        cursor.close()
        return stats
    
    def get_user_bills(self, flat_number):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM bills 
            WHERE flat_number = %s 
            ORDER BY created_at DESC
        """, (flat_number,))
        
        bills = cursor.fetchall()
        cursor.close()
        return bills
    
    def pay_bill(self, bill_id, payment_method):
        cursor = self.connection.cursor()
        
        cursor.execute("""
            UPDATE bills 
            SET payment_status = 'paid', payment_date = CURRENT_DATE, payment_method = %s
            WHERE bill_id = %s
        """, (payment_method, bill_id))
        
        cursor.close()
        return True
    
    def get_user_complaints(self, user_id):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM complaints 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        complaints = cursor.fetchall()
        cursor.close()
        return complaints
    
    def create_complaint(self, user_id, flat_number, title, description, category, priority):
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO complaints (user_id, flat_number, title, description, category, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING complaint_id
        """, (user_id, flat_number, title, description, category, priority))
        
        complaint_id = cursor.fetchone()[0]
        cursor.close()
        return complaint_id
    
    def get_unread_notifications(self, user_id):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT n.* FROM notifications n
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id 
                AND nr.user_id = %s
            WHERE nr.notification_id IS NULL
            ORDER BY n.created_at DESC
        """, (user_id,))
        
        notifications = cursor.fetchall()
        cursor.close()
        return notifications
    
    def mark_notification_read(self, notification_id, user_id):
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO notification_reads (notification_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (notification_id, user_id) DO NOTHING
        """, (notification_id, user_id))
        
        cursor.close()
        return True
    
    def close_connection(self):
        if self.connection:
            self.connection.close()
