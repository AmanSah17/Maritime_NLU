"""
Maritime Defense Dashboard - User Registration & Login Database
SQLite3 database for managing user accounts and authentication
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Tuple
import re

class UserDatabase:
    """Manages user registration and authentication"""
    
    DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.init_db()
    
    def get_connection(self):
        """Get database connection with thread-safe settings"""
        # Always create a new connection for thread safety with Streamlit
        conn = sqlite3.connect(self.DB_PATH, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0
                )
            """)

            # Create login history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logout_time TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
        finally:
            conn.close()

        # Create default admin user if not exists
        self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin user"""
        admin_email = "amansah1717@gmail.com"
        admin_password = "maritime_defense_2025"

        # Check if admin already exists
        if not self.user_exists(admin_email):
            conn = None
            try:
                conn = self.get_connection()
                cursor = conn.cursor()

                password_hash = self.hash_password(admin_password)

                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name, role)
                    VALUES (?, ?, ?, ?)
                """, (admin_email, password_hash, "Admin User", "admin"))

                conn.commit()
                print(f"✅ Default admin created: {admin_email}")
            except Exception as e:
                print(f"Note: Admin user may already exist: {e}")
            finally:
                if conn:
                    conn.close()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is valid"
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def register_user(self, email: str, password: str, full_name: str = "",
                     role: str = "user") -> Tuple[bool, str]:
        """Register a new user"""

        # Validate email
        if not self.validate_email(email):
            return False, "Invalid email format"

        # Validate password
        is_valid, message = self.validate_password(password)
        if not is_valid:
            return False, message

        # Check if user already exists
        if self.user_exists(email):
            return False, "Email already registered"

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            password_hash = self.hash_password(password)

            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (email, password_hash, full_name, role))

            conn.commit()

            # Log action
            user_id = cursor.lastrowid
            self.log_action(user_id, "user_registered", f"Email: {email}")

            return True, "User registered successfully"

        except Exception as e:
            return False, f"Registration error: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authenticate user with email and password"""
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, full_name, role, is_active, login_count
                FROM users WHERE email = ?
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return False, None
            
            # Check if user is active
            if not user['is_active']:
                return False, None
            
            # Verify password
            password_hash = self.hash_password(password)
            cursor.execute("""
                SELECT password_hash FROM users WHERE id = ?
            """, (user['id'],))
            
            stored_hash = cursor.fetchone()
            
            if not stored_hash or stored_hash['password_hash'] != password_hash:
                return False, None
            
            # Update last login and login count
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = ?
            """, (user['id'],))
            
            conn.commit()
            
            # Log login
            self.log_action(user['id'], "user_login", f"Email: {email}")
            
            user_data = {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role'],
                'login_count': user['login_count'] + 1
            }
            
            return True, user_data
        
        except Exception as e:
            print(f"Authentication error: {e}")
            return False, None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, full_name, role, is_active, created_at, last_login, login_count
                FROM users WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
        
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> Tuple[bool, str]:
        """Update user information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            allowed_fields = ['full_name', 'role', 'is_active']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False, "No valid fields to update"
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            cursor.execute(f"""
                UPDATE users SET {set_clause} WHERE id = ?
            """, values)
            
            conn.commit()
            
            self.log_action(user_id, "user_updated", str(updates))
            
            return True, "User updated successfully"
        
        except Exception as e:
            return False, f"Update error: {str(e)}"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verify old password
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "User not found"
            
            old_hash = self.hash_password(old_password)
            if user['password_hash'] != old_hash:
                return False, "Old password is incorrect"
            
            # Validate new password
            is_valid, message = self.validate_password(new_password)
            if not is_valid:
                return False, message
            
            # Update password
            new_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password_hash = ? WHERE id = ?
            """, (new_hash, user_id))
            
            conn.commit()
            
            self.log_action(user_id, "password_changed", "Password updated")
            
            return True, "Password changed successfully"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def log_action(self, user_id: Optional[int], action: str, details: str = ""):
        """Log user action"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, action, details))
            
            conn.commit()
        except Exception as e:
            print(f"Error logging action: {e}")
    
    def get_login_history(self, user_id: int, limit: int = 10) -> list:
        """Get user login history"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT login_time, logout_time, ip_address
                FROM login_history
                WHERE user_id = ?
                ORDER BY login_time DESC
                LIMIT ?
            """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            print(f"Error getting login history: {e}")
            return []
    
    def get_all_users(self) -> list:
        """Get all users (admin only)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, full_name, role, is_active, created_at, last_login, login_count
                FROM users
                ORDER BY created_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def deactivate_user(self, user_id: int) -> Tuple[bool, str]:
        """Deactivate user account"""
        return self.update_user(user_id, is_active=False)
    
    def activate_user(self, user_id: int) -> Tuple[bool, str]:
        """Activate user account"""
        return self.update_user(user_id, is_active=True)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Initialize database on import
user_db = UserDatabase()

