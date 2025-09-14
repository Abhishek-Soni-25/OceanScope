"""
Session Manager for handling Streamlit session state and user sessions.
"""
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time


class SessionManager:
    """Manages user sessions and Streamlit session state."""
    
    # Session timeout in minutes
    SESSION_TIMEOUT_MINUTES = 30
    
    @staticmethod
    def initialize_session() -> None:
        """Initialize session state variables if they don't exist."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        
        if 'session_start_time' not in st.session_state:
            st.session_state.session_start_time = None
        
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = None
    
    @staticmethod
    def login_user(user_data: Dict) -> None:
        """Log in a user and set session state."""
        current_time = datetime.now()
        
        st.session_state.authenticated = True
        st.session_state.user_data = user_data
        st.session_state.session_start_time = current_time
        st.session_state.last_activity = current_time
    
    @staticmethod
    def logout_user() -> None:
        """Log out user and clear session state."""
        # Clear all authentication-related session state
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.session_start_time = None
        st.session_state.last_activity = None
        
        # Clear any other session data that should not persist
        keys_to_clear = [
            'current_chat_session',
            'chat_messages',
            'chat_history',
            'selected_chat_id'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        SessionManager.initialize_session()
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """Get current user data."""
        if SessionManager.is_authenticated():
            return st.session_state.get('user_data')
        return None
    
    @staticmethod
    def get_user_id() -> Optional[int]:
        """Get current user ID."""
        user_data = SessionManager.get_current_user()
        return user_data.get('id') if user_data else None
    
    @staticmethod
    def get_username() -> Optional[str]:
        """Get current username."""
        user_data = SessionManager.get_current_user()
        return user_data.get('username') if user_data else None
    
    @staticmethod
    def update_activity() -> None:
        """Update last activity timestamp."""
        if SessionManager.is_authenticated():
            st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def is_session_expired() -> bool:
        """Check if session has expired."""
        if not SessionManager.is_authenticated():
            return True
        
        last_activity = st.session_state.get('last_activity')
        if not last_activity:
            return True
        
        # Check if session has expired
        timeout_delta = timedelta(minutes=SessionManager.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - last_activity > timeout_delta
    
    @staticmethod
    def validate_session() -> bool:
        """Validate current session and handle expiration."""
        SessionManager.initialize_session()
        
        if not SessionManager.is_authenticated():
            return False
        
        if SessionManager.is_session_expired():
            SessionManager.logout_user()
            return False
        
        # Update activity if session is valid
        SessionManager.update_activity()
        return True
    
    @staticmethod
    def require_authentication() -> bool:
        """Require authentication for protected pages."""
        if not SessionManager.validate_session():
            st.error("Please log in to access this page.")
            st.stop()
            return False
        return True
    
    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Get session information for debugging/monitoring."""
        return {
            'authenticated': SessionManager.is_authenticated(),
            'user_id': SessionManager.get_user_id(),
            'username': SessionManager.get_username(),
            'session_start_time': st.session_state.get('session_start_time'),
            'last_activity': st.session_state.get('last_activity'),
            'session_expired': SessionManager.is_session_expired()
        }
    
    @staticmethod
    def set_session_timeout(minutes: int) -> None:
        """Set session timeout in minutes."""
        SessionManager.SESSION_TIMEOUT_MINUTES = minutes
    
    @staticmethod
    def extend_session() -> None:
        """Extend session by updating last activity."""
        SessionManager.update_activity()