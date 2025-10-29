"""
Maritime Defense Dashboard - Authentication Page
User Registration and Login Interface
"""

import streamlit as st
from user_db import user_db
from auth_manager import AuthManager, SessionManager
from datetime import datetime

st.set_page_config(page_title="Authentication", layout="centered")

# Custom CSS for defense theme
st.markdown("""
<style>
:root {
    --primary-navy: #001F3F;
    --secondary-gray: #2C3E50;
    --accent-cyan: #00D9FF;
}

body {
    background: linear-gradient(135deg, #001F3F 0%, #2C3E50 100%);
    color: #E8E8E8;
    font-family: 'Courier New', monospace;
}

.stApp {
    background: linear-gradient(135deg, #001F3F 0%, #2C3E50 100%);
}

h1, h2, h3 {
    color: #00D9FF;
    text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
    letter-spacing: 2px;
}

.auth-container {
    background: rgba(44, 62, 80, 0.8);
    border: 2px solid #00D9FF;
    border-radius: 8px;
    padding: 30px;
    margin: 20px auto;
    max-width: 500px;
    box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
}

.auth-header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #00D9FF;
}

.password-requirements {
    background: rgba(0, 217, 255, 0.1);
    border-left: 4px solid #00D9FF;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
    font-size: 0.9em;
}

.requirement-item {
    margin: 5px 0;
    color: #E8E8E8;
}

.requirement-item.met {
    color: #00CC44;
}

.requirement-item.unmet {
    color: #FF9900;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
AuthManager.init_session_state()

# Try to restore from cookies first (on page load)
if not st.session_state.get("authenticated"):
    AuthManager.restore_from_cookies()

# Check if already logged in
if st.session_state.get("authenticated"):
    st.success(f"✅ Already logged in as {st.session_state.username}")
    if st.button("Go to Dashboard"):
        st.switch_page("pages/show_dataframes.py")
    if st.button("Logout"):
        AuthManager.logout()
        st.rerun()
else:
    # Auth tabs
    tab_login, tab_register = st.tabs(["🔓 Login", "📝 Register"])
    
    with tab_login:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header"><h2> Maritime Defense Dashboard</h2><p>Secure Login</p></div>', unsafe_allow_html=True)

        email = st.text_input("📧 Email Address", key="login_email")
        password = st.text_input("🔐 Password", type="password", key="login_password")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔓 Login", use_container_width=True, key="login_btn"):
                if email and password:
                    success, user_data = user_db.authenticate_user(email, password)

                    if success:
                        # Create JWT token
                        token = AuthManager.create_jwt_token(email)

                        # Update session state
                        st.session_state.auth_token = token
                        st.session_state.authenticated = True
                        st.session_state.username = email
                        st.session_state.user_data = user_data

                        # Save session to storage
                        AuthManager.save_session_to_storage()

                        # Save to cookies for persistence across browser refresh
                        AuthManager.save_to_cookies()

                        st.success(f" Welcome, {user_data.get('full_name', email)}!")
                        st.info("🍪 Your session has been saved. You'll stay logged in even after refreshing the page!")
                        st.balloons()

                        # Log action
                        user_db.log_action(user_data['id'], "dashboard_login", f"Logged in at {datetime.now()}")

                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")
                else:
                    st.warning("⚠️ Please enter email and password")

        with col2:
            if st.button("🔄 Clear", use_container_width=True, key="login_clear_btn"):
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        
    
    with tab_register:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header"><h2> Create Account</h2><p>Register for Maritime Defense Database</p></div>', unsafe_allow_html=True)
        
        full_name = st.text_input("👤 Full Name", key="reg_fullname")
        email = st.text_input("📧 Email Address", key="reg_email")
        password = st.text_input("🔐 Password", type="password", key="reg_password")
        password_confirm = st.text_input("🔐 Confirm Password", type="password", key="reg_password_confirm")
        
        # Password requirements checker
        st.markdown("**Password Requirements:**")
        
        if password:
            has_length = len(password) >= 8
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status = "✅" if has_length else "❌"
                st.markdown(f"{status} At least 8 characters")
            
            with col2:
                status = "✅" if has_upper else "❌"
                st.markdown(f"{status} Uppercase letter")
            
            with col3:
                status = "✅" if has_digit else "❌"
                st.markdown(f"{status} One digit")
        
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📝 Register", use_container_width=True, key="register_btn"):
                # Validation
                if not full_name:
                    st.error("❌ Please enter your full name")
                elif not email:
                    st.error("❌ Please enter your email")
                elif not password:
                    st.error("❌ Please enter a password")
                elif password != password_confirm:
                    st.error("❌ Passwords do not match")
                else:
                    # Register user
                    success, message = user_db.register_user(
                        email=email,
                        password=password,
                        full_name=full_name,
                        role="user"
                    )

                    if success:
                        st.success(f"✅ {message}")
                        st.info("You can now login with your credentials")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")

        with col2:
            if st.button("🔄 Clear", use_container_width=True, key="register_clear_btn"):
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
