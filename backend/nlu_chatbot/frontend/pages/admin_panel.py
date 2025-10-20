"""
Maritime Defense Dashboard - Admin Panel
User Management and System Administration
"""

import streamlit as st
import pandas as pd
from user_db import user_db
from auth_manager import AuthManager, SessionManager
from datetime import datetime

st.set_page_config(page_title="Admin Panel", layout="wide")

# Custom CSS
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

.admin-header {
    background: linear-gradient(90deg, #001F3F 0%, #2C3E50 50%, #001F3F 100%);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    text-align: center;
}

.user-card {
    background: rgba(44, 62, 80, 0.7);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
}

.status-active {
    color: #00CC44;
    text-shadow: 0 0 10px rgba(0, 204, 68, 0.5);
}

.status-inactive {
    color: #FF9900;
    text-shadow: 0 0 10px rgba(255, 153, 0, 0.5);
}
</style>
""", unsafe_allow_html=True)

# Initialize session
AuthManager.init_session_state()

# Check authentication
if not st.session_state.get("authenticated"):
    st.error("❌ Please login first")
    if st.button("Go to Login"):
        st.switch_page("pages/auth.py")
    st.stop()

# Check admin role
user_data = st.session_state.get("user_data", {})
if user_data.get("role") != "admin":
    st.error("❌ Admin access required")
    st.stop()

st.markdown('<div class="admin-header"><h1>⚙️ ADMIN PANEL - USER MANAGEMENT</h1></div>', unsafe_allow_html=True)

# Admin tabs
tab_users, tab_stats, tab_settings = st.tabs(["👥 Users", "📊 Statistics", "⚙️ Settings"])

with tab_users:
    st.subheader("User Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Users"):
            st.rerun()
    
    with col2:
        search_email = st.text_input("Search by email", key="search_email")
    
    with col3:
        filter_role = st.selectbox("Filter by role", ["All", "admin", "user"], key="filter_role")
    
    # Get all users
    all_users = user_db.get_all_users()
    
    if all_users:
        # Filter users
        filtered_users = all_users
        
        if search_email:
            filtered_users = [u for u in filtered_users if search_email.lower() in u['email'].lower()]
        
        if filter_role != "All":
            filtered_users = [u for u in filtered_users if u['role'] == filter_role]
        
        # Display users
        st.markdown("---")
        
        for user in filtered_users:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{user['full_name']}**")
                    st.caption(user['email'])
                
                with col2:
                    status = "🟢 Active" if user['is_active'] else "🔴 Inactive"
                    st.markdown(f"{status}")
                    st.caption(f"Role: `{user['role']}`")
                
                with col3:
                    st.metric("Logins", user['login_count'])
                
                with col4:
                    if user['last_login']:
                        st.caption(f"Last: {user['last_login'][:10]}")
                    else:
                        st.caption("Never")
                
                with col5:
                    if st.button("⋮", key=f"menu_{user['id']}"):
                        st.session_state[f"show_menu_{user['id']}"] = True
                
                # User actions menu
                if st.session_state.get(f"show_menu_{user['id']}"):
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if user['is_active']:
                            if st.button("🔒 Deactivate", key=f"deactivate_{user['id']}"):
                                user_db.deactivate_user(user['id'])
                                st.success(f"✅ User deactivated")
                                st.rerun()
                        else:
                            if st.button("🔓 Activate", key=f"activate_{user['id']}"):
                                user_db.activate_user(user['id'])
                                st.success(f"✅ User activated")
                                st.rerun()
                    
                    with action_col2:
                        if st.button("📋 View History", key=f"history_{user['id']}"):
                            history = user_db.get_login_history(user['id'])
                            if history:
                                history_df = pd.DataFrame(history)
                                st.dataframe(history_df, use_container_width=True)
                            else:
                                st.info("No login history")
                    
                    with action_col3:
                        if st.button("🗑️ Delete", key=f"delete_{user['id']}"):
                            st.warning("Delete functionality requires confirmation")
                
                st.markdown("---")
        
        # Summary
        st.markdown("### Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(all_users))
        
        with col2:
            active_count = sum(1 for u in all_users if u['is_active'])
            st.metric("Active Users", active_count)
        
        with col3:
            admin_count = sum(1 for u in all_users if u['role'] == 'admin')
            st.metric("Admins", admin_count)
        
        with col4:
            total_logins = sum(u['login_count'] for u in all_users)
            st.metric("Total Logins", total_logins)
    
    else:
        st.info("No users found")

with tab_stats:
    st.subheader("System Statistics")
    
    all_users = user_db.get_all_users()
    
    if all_users:
        # Create statistics dataframe
        stats_data = {
            'Metric': [
                'Total Users',
                'Active Users',
                'Inactive Users',
                'Admin Users',
                'Regular Users',
                'Total Logins',
                'Avg Logins per User'
            ],
            'Value': [
                len(all_users),
                sum(1 for u in all_users if u['is_active']),
                sum(1 for u in all_users if not u['is_active']),
                sum(1 for u in all_users if u['role'] == 'admin'),
                sum(1 for u in all_users if u['role'] == 'user'),
                sum(u['login_count'] for u in all_users),
                round(sum(u['login_count'] for u in all_users) / len(all_users), 2) if all_users else 0
            ]
        }
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)
        
        # User creation timeline
        st.markdown("---")
        st.subheader("User Creation Timeline")
        
        users_by_date = {}
        for user in all_users:
            date = user['created_at'][:10]
            users_by_date[date] = users_by_date.get(date, 0) + 1
        
        timeline_df = pd.DataFrame(list(users_by_date.items()), columns=['Date', 'New Users'])
        st.bar_chart(timeline_df.set_index('Date'))

with tab_settings:
    st.subheader("System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Database Information**")
        st.info(f"""
        - Database: `users.db`
        - Location: `frontend/users.db`
        - Type: SQLite3
        """)
    
    with col2:
        st.markdown("**Security Settings**")
        st.info(f"""
        - Password Hashing: SHA-256
        - Min Password Length: 8 characters
        - Token Expiry: 24 hours
        - Algorithm: HS256
        """)
    
    st.markdown("---")
    
    st.markdown("**Maintenance**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Database"):
            st.success("✅ Database refreshed")
    
    with col2:
        if st.button("📊 Export Users"):
            all_users = user_db.get_all_users()
            users_df = pd.DataFrame(all_users)
            csv = users_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="users_export.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🔐 Reset Admin Password"):
            st.warning("This will reset admin password to default")
            if st.button("Confirm Reset"):
                user_db.create_default_admin()
                st.success("✅ Admin password reset")

# Logout button
st.markdown("---")
if st.button("🔓 Logout"):
    AuthManager.logout()
    st.success("✅ Logged out")
    st.rerun()

