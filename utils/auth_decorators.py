"""
Authentication decorators and utilities for Streamlit pages.
"""
import streamlit as st
from functools import wraps
from typing import Callable, Any
from .session_manager import SessionManager


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for Streamlit page functions.
    
    Usage:
        @require_auth
        def my_page():
            st.write("This page requires authentication")
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if not SessionManager.validate_session():
            st.error("🔒 Please log in to access this page.")
            st.info("You will be redirected to the login page.")
            st.stop()
            return None
        
        # Update activity on each page access
        SessionManager.update_activity()
        return func(*args, **kwargs)
    
    return wrapper


def auth_optional(func: Callable) -> Callable:
    """
    Decorator for pages where authentication is optional but session should be validated.
    
    Usage:
        @auth_optional
        def my_page():
            if SessionManager.is_authenticated():
                st.write(f"Welcome back, {SessionManager.get_username()}!")
            else:
                st.write("Welcome, guest!")
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Initialize session but don't require authentication
        SessionManager.initialize_session()
        
        # Validate session if authenticated (handles expiration)
        if SessionManager.is_authenticated():
            SessionManager.validate_session()
        
        return func(*args, **kwargs)
    
    return wrapper


def show_user_profile_header():
    """Display user profile in the application header."""
    if SessionManager.is_authenticated():
        user_data = SessionManager.get_current_user()
        
        # Create header with user profile
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"👋 **Welcome back, {user_data['username']}!**")
        
        with col2:
            # User profile info button
            if st.button("👤 Profile", help="View profile information"):
                show_user_profile_modal()
        
        with col3:
            # Logout button
            if st.button("🚪 Logout", type="primary", help="Logout and return to landing page"):
                logout_user_with_redirect()
        
        st.markdown("---")
    else:
        # Show login/signup options for unauthenticated users
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("🔓 **Not logged in**")
        
        with col2:
            if st.button("🔑 Login", type="primary"):
                st.switch_page("pages/login.py")
        
        with col3:
            if st.button("📝 Sign Up", type="secondary"):
                st.switch_page("pages/signup.py")
        
        st.markdown("---")


def show_user_profile_modal():
    """Display user profile information in a modal-like expander."""
    if SessionManager.is_authenticated():
        user_data = SessionManager.get_current_user()
        session_info = SessionManager.get_session_info()
        
        with st.expander("👤 User Profile", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Account Information**")
                st.write(f"**Username:** {user_data['username']}")
                st.write(f"**Email:** {user_data['email']}")
                st.write(f"**Member Since:** {user_data['created_at'][:10]}")
            
            with col2:
                st.write("**Session Information**")
                st.write(f"**User ID:** {session_info['user_id']}")
                if session_info['session_start_time']:
                    start_time = session_info['session_start_time'].strftime("%H:%M:%S")
                    st.write(f"**Session Started:** {start_time}")
                if session_info['last_activity']:
                    last_activity = session_info['last_activity'].strftime("%H:%M:%S")
                    st.write(f"**Last Activity:** {last_activity}")
            
            # Session management options
            st.markdown("**Session Management**")
            col_extend, col_logout = st.columns(2)
            
            with col_extend:
                if st.button("🔄 Extend Session", help="Reset session timeout", key="extend_session_modal"):
                    SessionManager.extend_session()
                    st.success("Session extended!")
                    st.rerun()
            
            with col_logout:
                if st.button("🚪 Logout Now", type="secondary", help="Logout immediately", key="logout_modal"):
                    logout_user_with_redirect()


def logout_user_with_redirect():
    """Logout user with proper session cleanup and redirect to landing page."""
    try:
        # Clear session data
        SessionManager.logout_user()
        
        # Show logout success message
        st.success("✅ Successfully logged out!")
        st.info("Redirecting to landing page...")
        
        # Force redirect to landing page
        st.switch_page("pages/landing.py")
        
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")
        # Force redirect even if there's an error
        st.switch_page("pages/landing.py")


def show_auth_status():
    """Display authentication status in sidebar."""
    with st.sidebar:
        if SessionManager.is_authenticated():
            user_data = SessionManager.get_current_user()
            st.success(f"✅ Logged in as: **{user_data['username']}**")
            
            # Show session info
            with st.expander("Session Info", expanded=False):
                session_info = SessionManager.get_session_info()
                st.write(f"**User ID:** {session_info['user_id']}")
                st.write(f"**Session Start:** {session_info['session_start_time']}")
                st.write(f"**Last Activity:** {session_info['last_activity']}")
            
            # Logout button
            if st.button("🚪 Logout", type="secondary"):
                logout_user_with_redirect()
        else:
            st.warning("🔓 Not logged in")
            if st.button("🔑 Go to Login", type="primary"):
                st.switch_page("pages/login.py")


def check_session_expiry():
    """Check for session expiry and show warning."""
    if SessionManager.is_authenticated():
        if SessionManager.is_session_expired():
            st.error("⏰ Your session has expired. Please log in again.")
            SessionManager.logout_user()
            st.rerun()


def extend_session_button():
    """Show a button to extend the current session."""
    if SessionManager.is_authenticated():
        with st.sidebar:
            if st.button("🔄 Extend Session", help="Reset session timeout"):
                SessionManager.extend_session()
                st.success("Session extended!")
                st.rerun()


class AuthMiddleware:
    """Middleware class for handling authentication in Streamlit apps."""
    
    @staticmethod
    def initialize():
        """Initialize authentication middleware."""
        SessionManager.initialize_session()
    
    @staticmethod
    def check_auth_redirect():
        """Check authentication and redirect if needed."""
        # Get current page from session state or URL
        current_page = st.session_state.get("current_page", "")
        
        # Pages that don't require authentication
        public_pages = ["login.py", "signup.py", "landing.py"]
        
        # Check if current page requires authentication
        if not any(page in current_page for page in public_pages):
            if not SessionManager.validate_session():
                st.error("🔒 Session expired or authentication required")
                st.info("Please log in to continue")
                if st.button("🔑 Go to Login", type="primary"):
                    st.switch_page("pages/login.py")
                st.stop()
    
    @staticmethod
    def setup_page_auth(require_auth: bool = True, page_name: str = None, show_header: bool = True):
        """Set up authentication for a page."""
        AuthMiddleware.initialize()
        
        # Track current page for session persistence
        if page_name:
            st.session_state.current_page = page_name
        
        if require_auth:
            if not SessionManager.validate_session():
                # Store intended page for redirect after login
                if page_name:
                    st.session_state.intended_page = f"pages/{page_name}"
                
                st.error("🔒 Authentication required")
                st.info("Please log in to access this page.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔑 Login", type="primary"):
                        st.switch_page("pages/login.py")
                with col2:
                    if st.button("📝 Sign Up", type="secondary"):
                        st.switch_page("pages/signup.py")
                
                st.stop()
        
        # Show user profile header for authenticated users
        if show_header:
            show_user_profile_header()
        
        # Show auth status in sidebar
        show_auth_status()
        
        # Check for session expiry
        check_session_expiry()
        
        # Update activity timestamp for session persistence
        SessionManager.update_activity()


def get_user_context():
    """Get current user context for the application."""
    if not SessionManager.is_authenticated():
        return None
    
    return {
        'user_id': SessionManager.get_user_id(),
        'username': SessionManager.get_username(),
        'user_data': SessionManager.get_current_user(),
        'session_info': SessionManager.get_session_info()
    }


def show_user_identification_in_chat():
    """Display user identification in chat interface."""
    if SessionManager.is_authenticated():
        user_data = SessionManager.get_current_user()
        
        # Create a subtle user identification banner
        st.markdown(f"""
        <div style="
            background-color: #f0f2f6; 
            padding: 8px 12px; 
            border-radius: 5px; 
            border-left: 4px solid #1f77b4;
            margin-bottom: 10px;
        ">
            <small>💬 <strong>Chatting as:</strong> {user_data['username']} | 
            <strong>User ID:</strong> {user_data['id']}</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("🔓 Not authenticated - chat functionality may be limited")