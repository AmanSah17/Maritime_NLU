"""
Maritime Defense Dashboard - Authentication & Session Management
Handles JWT tokenization and session state persistence
"""

import streamlit as st
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import base64

class AuthManager:
    """Manages JWT tokens and session state for admin users"""
    
    # Secret key for JWT (in production, use environment variable)
    SECRET_KEY = "maritime_defense_secret_2025"
    
    # Admin credentials (in production, use database)
    ADMIN_USERS = {
        "admin": "maritime_defense_2025",
        "operator": "operator_2025"
    }
    
    @staticmethod
    def create_jwt_token(username: str, expires_in_hours: int = 24) -> str:
        """Create a JWT token for the user"""
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        
        payload = {
            "username": username,
            "iat": datetime.utcnow().isoformat(),
            "exp": (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat(),
            "role": "admin"
        }
        
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            AuthManager.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        # Return complete JWT
        token = f"{message}.{signature_encoded}"
        return token
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_encoded, payload_encoded, signature_encoded = parts
            
            # Verify signature
            message = f"{header_encoded}.{payload_encoded}"
            expected_signature = hmac.new(
                AuthManager.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            
            expected_signature_encoded = base64.urlsafe_b64encode(
                expected_signature
            ).decode().rstrip('=')
            
            if signature_encoded != expected_signature_encoded:
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(
                payload_encoded + '=' * (4 - len(payload_encoded) % 4)
            ).decode()
            
            payload = json.loads(payload_json)
            
            # Check expiration
            exp_time = datetime.fromisoformat(payload['exp'])
            if datetime.utcnow() > exp_time:
                return None
            
            return payload
        
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        if username in AuthManager.ADMIN_USERS:
            if AuthManager.ADMIN_USERS[username] == password:
                token = AuthManager.create_jwt_token(username)
                return token
        return None
    
    @staticmethod
    def init_session_state():
        """Initialize session state for authentication"""
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        if "username" not in st.session_state:
            st.session_state.username = None
        
        if "dashboard_state" not in st.session_state:
            st.session_state.dashboard_state = {
                "selected_vessel": None,
                "track_data": None,
                "last_query": None,
                "last_update": None,
                "interaction_history": []
            }
        
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {
                "theme": "defense",
                "auto_refresh": True,
                "refresh_interval": 30,
                "map_zoom": 12,
                "show_track_arrows": True,
                "show_statistics": True
            }
    
    @staticmethod
    def save_session_to_storage():
        """Save session state to browser storage (via Streamlit)"""
        session_data = {
            "auth_token": st.session_state.get("auth_token"),
            "username": st.session_state.get("username"),
            "dashboard_state": st.session_state.get("dashboard_state"),
            "user_preferences": st.session_state.get("user_preferences"),
            "saved_at": datetime.utcnow().isoformat()
        }
        
        # Store in session state (persists during session)
        st.session_state.session_backup = session_data
        
        return session_data
    
    @staticmethod
    def restore_session_from_storage():
        """Restore session state from storage"""
        if "session_backup" in st.session_state:
            backup = st.session_state.session_backup
            
            # Verify token is still valid
            if backup.get("auth_token"):
                payload = AuthManager.verify_jwt_token(backup["auth_token"])
                if payload:
                    st.session_state.auth_token = backup["auth_token"]
                    st.session_state.username = backup["username"]
                    st.session_state.authenticated = True
                    st.session_state.dashboard_state = backup.get("dashboard_state", {})
                    st.session_state.user_preferences = backup.get("user_preferences", {})
                    return True
        
        return False
    
    @staticmethod
    def update_interaction_history(action: str, details: Dict[str, Any]):
        """Track user interactions for audit trail"""
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "username": st.session_state.get("username")
        }
        
        if "interaction_history" not in st.session_state.dashboard_state:
            st.session_state.dashboard_state["interaction_history"] = []
        
        st.session_state.dashboard_state["interaction_history"].append(interaction)
        
        # Keep only last 100 interactions
        if len(st.session_state.dashboard_state["interaction_history"]) > 100:
            st.session_state.dashboard_state["interaction_history"] = \
                st.session_state.dashboard_state["interaction_history"][-100:]
    
    @staticmethod
    def get_interaction_history() -> list:
        """Get user interaction history"""
        return st.session_state.dashboard_state.get("interaction_history", [])
    
    @staticmethod
    def logout():
        """Logout user and clear session"""
        st.session_state.auth_token = None
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.dashboard_state = {
            "selected_vessel": None,
            "track_data": None,
            "last_query": None,
            "last_update": None,
            "interaction_history": []
        }


class SessionManager:
    """Manages dashboard session state and persistence"""
    
    @staticmethod
    def save_vessel_selection(vessel_name: str, vessel_data: Dict[str, Any]):
        """Save selected vessel to session"""
        st.session_state.dashboard_state["selected_vessel"] = {
            "name": vessel_name,
            "data": vessel_data,
            "selected_at": datetime.utcnow().isoformat()
        }
        AuthManager.update_interaction_history("vessel_selected", {"vessel": vessel_name})
    
    @staticmethod
    def save_track_data(track_data: list):
        """Save track data to session"""
        st.session_state.dashboard_state["track_data"] = {
            "data": track_data,
            "saved_at": datetime.utcnow().isoformat(),
            "point_count": len(track_data)
        }
        AuthManager.update_interaction_history("track_loaded", {"points": len(track_data)})
    
    @staticmethod
    def get_current_vessel() -> Optional[Dict[str, Any]]:
        """Get currently selected vessel"""
        return st.session_state.dashboard_state.get("selected_vessel")
    
    @staticmethod
    def get_current_track() -> Optional[list]:
        """Get current track data"""
        track_info = st.session_state.dashboard_state.get("track_data")
        if track_info:
            return track_info.get("data")
        return None
    
    @staticmethod
    def update_last_query(query_text: str, results: Dict[str, Any]):
        """Update last query information"""
        st.session_state.dashboard_state["last_query"] = {
            "text": query_text,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def update_last_update_time():
        """Update last update timestamp"""
        st.session_state.dashboard_state["last_update"] = datetime.utcnow().isoformat()
    
    @staticmethod
    def get_session_summary() -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "username": st.session_state.get("username"),
            "authenticated": st.session_state.get("authenticated"),
            "selected_vessel": st.session_state.dashboard_state.get("selected_vessel"),
            "track_points": len(st.session_state.dashboard_state.get("track_data", {}).get("data", [])),
            "last_update": st.session_state.dashboard_state.get("last_update"),
            "interaction_count": len(st.session_state.dashboard_state.get("interaction_history", []))
        }

