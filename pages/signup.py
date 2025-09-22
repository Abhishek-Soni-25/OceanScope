import streamlit as st
import re
import time
from utils.auth_manager import AuthManager
from utils.async_wrapper import run_auth_operation
from utils.ui_feedback import UIFeedback, LoadingStates, ErrorMessages, SuccessMessages

# Configure page
st.set_page_config(
    page_title="Sign Up - OceanScope",
    page_icon="📝",
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
    
    .signup-container {
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
    
    .password-strength {
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
    
    .strength-weak { color: #ff6b6b !important; }
    .strength-medium { color: #ffd43b !important; }
    .strength-strong { color: #51cf66 !important; }
    
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

st.markdown("# 📝 Join OceanScope")

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format and requirements."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    return True, "Username is valid"

def get_password_strength(password: str) -> tuple[str, str]:
    """Get password strength and color class."""
    if len(password) < 6:
        return "Very Weak", "strength-weak"
    
    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    
    if score < 2:
        return "Weak", "strength-weak"
    elif score < 4:
        return "Medium", "strength-medium"
    else:
        return "Strong", "strength-strong"

# Signup form
with st.container():
    st.markdown("""
    <div class="signup-container">
        <h3 style="text-align: center; margin-bottom: 2rem; color: #ffffff !important;">Create Your Account</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize form state
    if 'signup_errors' not in st.session_state:
        st.session_state.signup_errors = {}
    if 'signup_success' not in st.session_state:
        st.session_state.signup_success = False
    
    # Form fields
    username = st.text_input(
        "Username", 
        placeholder="Choose a unique username (3-50 characters)",
        help="Username can contain letters, numbers, underscores, and hyphens"
    )
    
    # Username validation feedback
    if username:
        is_valid, message = validate_username(username)
        if not is_valid:
            st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
    
    email = st.text_input(
        "Email", 
        placeholder="Enter your email address",
        help="We'll use this for account recovery and important notifications"
    )
    
    # Email validation feedback
    if email and not validate_email(email):
        st.markdown('<div class="error-message">❌ Please enter a valid email address</div>', unsafe_allow_html=True)
    
    password = st.text_input(
        "Password", 
        type="password", 
        placeholder="Create a strong password",
        help="Password should be at least 8 characters with uppercase, lowercase, and numbers"
    )
    
    # Password strength indicator
    if password:
        strength, strength_class = get_password_strength(password)
        st.markdown(f'<div class="password-strength {strength_class}">Password Strength: {strength}</div>', unsafe_allow_html=True)
        
        # Password requirements check
        is_strong, strength_message = auth_manager.validate_password_strength(password)
        if not is_strong:
            st.markdown(f'<div class="error-message">❌ {strength_message}</div>', unsafe_allow_html=True)
    
    confirm_password = st.text_input(
        "Confirm Password", 
        type="password", 
        placeholder="Confirm your password"
    )
    
    # Password confirmation check
    if password and confirm_password and password != confirm_password:
        st.markdown('<div class="error-message">❌ Passwords do not match</div>', unsafe_allow_html=True)
    
    # Terms and conditions
    agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
    
    # Display any previous errors
    if st.session_state.signup_errors:
        for error in st.session_state.signup_errors.values():
            st.markdown(f'<div class="error-message">❌ {error}</div>', unsafe_allow_html=True)
    
    # Display success message
    if st.session_state.signup_success:
        st.markdown('<div class="success-message">✅ Account created successfully! Redirecting...</div>', unsafe_allow_html=True)
        st.balloons()
        # Clear success state and redirect after a short delay
        st.session_state.signup_success = False
        st.rerun()
    
    # Sign up button
    if st.button("🚀 Create Account", type="primary", use_container_width=True):
        # Clear previous errors
        st.session_state.signup_errors = {}
        
        # Validate all fields
        errors = {}
        
        if not username:
            errors['username'] = ErrorMessages.AUTH_REQUIRED_FIELD
        else:
            is_valid, message = validate_username(username)
            if not is_valid:
                errors['username'] = message
        
        if not email:
            errors['email'] = ErrorMessages.AUTH_REQUIRED_FIELD
        elif not validate_email(email):
            errors['email'] = "Please enter a valid email address"
        
        if not password:
            errors['password'] = ErrorMessages.AUTH_REQUIRED_FIELD
        else:
            is_strong, strength_message = auth_manager.validate_password_strength(password)
            if not is_strong:
                errors['password'] = strength_message
        
        if not confirm_password:
            errors['confirm_password'] = "Please confirm your password"
        elif password != confirm_password:
            errors['confirm_password'] = "Passwords do not match"
        
        if not agree_terms:
            errors['terms'] = "You must agree to the Terms of Service and Privacy Policy"
        
        # If no validation errors, attempt registration
        if not errors:
            try:
                # Show loading state with proper feedback
                with UIFeedback.loading_state(LoadingStates.AUTH_REGISTER):
                    success, message = run_auth_operation(
                        lambda auth_mgr, u, e, p: auth_mgr.register_user(u, e, p),
                        username, email, password
                    )
                
                if success:
                    st.session_state.signup_success = True
                    
                    # Show success message
                    UIFeedback.show_success(SuccessMessages.AUTH_REGISTER_SUCCESS)
                    st.balloons()
                    
                    # Small delay to show success message
                    time.sleep(1)
                    
                    # Auto-login the user after successful registration
                    try:
                        with UIFeedback.loading_state("Logging you in..."):
                            login_success, login_message = run_auth_operation(
                                lambda auth_mgr, u, p: auth_mgr.login_user_with_session(u, p),
                                username, password
                            )
                        
                        if login_success:
                            st.switch_page("pages/chatbot.py")
                        else:
                            UIFeedback.show_warning("Account created but auto-login failed. Please log in manually.")
                            time.sleep(2)
                            st.switch_page("pages/login.py")
                    except Exception as e:
                        UIFeedback.show_warning("Account created successfully! Please log in.")
                        time.sleep(2)
                        st.switch_page("pages/login.py")
                else:
                    # Registration failed with specific message
                    errors['registration'] = message
            
            except Exception as e:
                errors['registration'] = ErrorMessages.UNEXPECTED_ERROR
                print(f"Registration error: {e}")
        
        # Store errors in session state
        st.session_state.signup_errors = errors
        
        if errors:
            st.rerun()
    
    st.markdown("---")
    
    # Login link
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align: center; color: #ffffff;">Already have an account?</div>', unsafe_allow_html=True)
        
        if st.button("🔑 Login to Existing Account", use_container_width=True):
            st.switch_page("pages/login.py")