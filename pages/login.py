import streamlit as st
import time
from utils.auth_manager import AuthManager
from utils.async_wrapper import run_auth_operation
from utils.ui_feedback import UIFeedback, LoadingStates, ErrorMessages, SuccessMessages

# Configure page
st.set_page_config(
    page_title="Login - OceanScope",
    page_icon="🔑",
    layout="centered"
)

# Custom CSS with dark theme
st.markdown("""
<style>
    /* Force dark background and white text */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: #1a1a1a !important;
        color: #ffffff !important;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(255,255,255,0.1);
        border: 1px solid #333333;
    }
    
    .back-button {
        margin-bottom: 2rem;
    }
    
    .error-message {
        color: #ff6b6b !important;
        background-color: #2d1b1b !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ff6b6b;
        margin: 0.5rem 0;
    }
    
    .success-message {
        color: #51cf66 !important;
        background-color: #1b2d1b !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #51cf66;
        margin: 0.5rem 0;
    }
    
    .info-message {
        color: #74c0fc !important;
        background-color: #1b1f2d !important;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #74c0fc;
        margin: 0.5rem 0;
    }
    
    /* Override Streamlit's default text colors */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #ffffff !important;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #555555 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #555555 !important;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize auth manager
auth_manager = AuthManager()

# Initialize session management
from utils.session_manager import SessionManager
SessionManager.initialize_session()

# Check if user is already authenticated
if SessionManager.is_authenticated():
    st.switch_page("pages/chatbot.py")

# Back to landing page button
if st.button("← Back to Home", key="back_to_landing"):
    st.switch_page("pages/landing.py")

st.markdown("# 🔑 Login to OceanScope")

# Login form
with st.container():
    st.markdown("""
    <div class="login-container">
        <h3 style="text-align: center; margin-bottom: 2rem; color: #ffffff !important;">Welcome Back!</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize form state
    if 'login_errors' not in st.session_state:
        st.session_state.login_errors = {}
    if 'login_success' not in st.session_state:
        st.session_state.login_success = False
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    # Check for too many failed attempts
    max_attempts = 5
    if st.session_state.login_attempts >= max_attempts:
        st.markdown(f'<div class="error-message">❌ Too many failed login attempts. Please wait before trying again.</div>', unsafe_allow_html=True)
        if st.button("Reset Attempts", type="secondary"):
            st.session_state.login_attempts = 0
            st.rerun()
    else:
        # Form fields
        username = st.text_input(
            "Username or Email", 
            placeholder="Enter your username or email",
            help="You can use either your username or email address to log in"
        )
        
        password = st.text_input(
            "Password", 
            type="password", 
            placeholder="Enter your password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            remember_me = st.checkbox("Remember me", help="Keep me logged in for longer")
        
        with col2:
            st.markdown('<div style="text-align: right; margin-top: 1.5rem;"><small style="color: #cccccc;">Forgot password? Contact support</small></div>', unsafe_allow_html=True)
        
        # Display any previous errors
        if st.session_state.login_errors:
            for error in st.session_state.login_errors.values():
                st.markdown(f'<div class="error-message">❌ {error}</div>', unsafe_allow_html=True)
        
        # Display success message
        if st.session_state.login_success:
            st.markdown('<div class="success-message">✅ Login successful! Redirecting...</div>', unsafe_allow_html=True)
            st.session_state.login_success = False
            st.rerun()
        
        # Login button
        if st.button("🚀 Login", type="primary", use_container_width=True):
            # Clear previous errors
            st.session_state.login_errors = {}
            
            # Validate fields
            errors = {}
            
            if not username:
                errors['username'] = ErrorMessages.AUTH_REQUIRED_FIELD
            elif len(username.strip()) < 3:
                errors['username'] = "Username or email must be at least 3 characters"
            
            if not password:
                errors['password'] = ErrorMessages.AUTH_REQUIRED_FIELD
            elif len(password) < 1:
                errors['password'] = "Password cannot be empty"
            
            # If no validation errors, attempt authentication
            if not errors:
                try:
                    # Show loading state with proper feedback
                    with UIFeedback.loading_state(LoadingStates.AUTH_LOGIN):
                        success, message = run_auth_operation(
                            lambda auth_mgr, u, p: auth_mgr.login_user_with_session(u, p),
                            username.strip(), password
                        )
                    
                    if success:
                        st.session_state.login_success = True
                        st.session_state.login_attempts = 0  # Reset attempts on success
                        
                        # Show success message
                        UIFeedback.show_success(SuccessMessages.AUTH_LOGIN_SUCCESS)
                        
                        # Extend session if remember me is checked
                        if remember_me:
                            from utils.session_manager import SessionManager
                            SessionManager.set_session_timeout(60 * 24 * 7)  # 7 days
                            UIFeedback.show_info("Session extended for 7 days")
                        
                        # Small delay to show success message
                        time.sleep(1)
                        
                        # Redirect to intended page or default to chatbot
                        intended_page = st.session_state.get("intended_page", "pages/chatbot.py")
                        st.switch_page(intended_page)
                    else:
                        st.session_state.login_attempts += 1
                        remaining_attempts = max_attempts - st.session_state.login_attempts
                        
                        if remaining_attempts > 0:
                            errors['authentication'] = f"{message} ({remaining_attempts} attempts remaining)"
                        else:
                            errors['authentication'] = "Too many failed attempts. Please wait before trying again."
                
                except Exception as e:
                    errors['authentication'] = ErrorMessages.UNEXPECTED_ERROR
                    print(f"Login error: {e}")
            
            # Store errors in session state
            st.session_state.login_errors = errors
            
            if errors:
                st.rerun()
    
    st.markdown("---")
    
    # Sign up link
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align: center; color: #ffffff;">Don\'t have an account?</div>', unsafe_allow_html=True)
        
        if st.button("📝 Create New Account", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    # Additional info for demo/testing
    if st.session_state.login_attempts > 0:
        st.markdown(f'<div class="info-message">ℹ️ Failed attempts: {st.session_state.login_attempts}/{max_attempts}</div>', unsafe_allow_html=True)