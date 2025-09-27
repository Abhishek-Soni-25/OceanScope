import streamlit as st
import re
from utils.auth_manager import AuthManager
from utils.session_manager import SessionManager

# --- Page config ---
st.set_page_config(page_title="Sign Up - OceanScope", page_icon="📝", layout="centered")

# --- Dark theme CSS ---
st.markdown("""
<style>
.stApp { background-color:#000;color:#fff; }
.signup-container { max-width:400px;margin:2rem auto;padding:2rem;background:#1a1a1a;border-radius:10px;box-shadow:0 4px 6px rgba(255,255,255,0.1);border:1px solid #333; }
.stTextInput > div > div > input { background:#2d2d2d;color:#fff;border:1px solid #555; }
.stButton > button { background:#2d2d2d;color:#fff;border:1px solid #555; }
.error-message { color:#ff6b6b;background:#2d1b1b;padding:0.5rem;border-radius:5px;border-left:4px solid #ff6b6b;margin:0.5rem 0; }
.success-message { color:#51cf66;background:#1b2d1b;padding:0.5rem;border-radius:5px;border-left:4px solid #51cf66;margin:0.5rem 0; }
.password-strength { font-size:0.8rem;margin-top:0.25rem; }
.strength-weak { color:#ff6b6b!important; }
.strength-medium { color:#ffd43b!important; }
.strength-strong { color:#51cf66!important; }
</style>
""", unsafe_allow_html=True)

# --- Initialize ---
auth_manager = AuthManager()
SessionManager.initialize_session()

if SessionManager.is_authenticated():
    st.experimental_rerun()  # Redirect if already logged in

st.markdown('<div class="signup-container"><h3 style="text-align:center;">Create Your Account</h3></div>', unsafe_allow_html=True)

# --- Helper functions ---
def validate_email(email): return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)
def password_strength(pw):
    score = sum([len(pw)>=8, any(c.isupper() for c in pw), any(c.islower() for c in pw), any(c.isdigit() for c in pw), any(c in "!@#$%^&*()" for c in pw)])
    if score<2: return "Very Weak","strength-weak"
    if score<4: return "Medium","strength-medium"
    return "Strong","strength-strong"

# --- Form ---
username = st.text_input("Username", placeholder="3-50 chars, letters/numbers/_/-")
email = st.text_input("Email", placeholder="Enter your email")
password = st.text_input("Password", type="password", placeholder="Min 8 chars, upper/lower/digit")
confirm_password = st.text_input("Confirm Password", type="password")
agree_terms = st.checkbox("I agree to Terms of Service & Privacy Policy")

# --- Real-time feedback ---
if username and (len(username)<3 or len(username)>50 or not re.match(r'^[\w-]+$', username)):
    st.markdown('<div class="error-message">Invalid username</div>', unsafe_allow_html=True)
if email and not validate_email(email):
    st.markdown('<div class="error-message">Invalid email</div>', unsafe_allow_html=True)
if password:
    strength,label = password_strength(password)
    st.markdown(f'<div class="password-strength {label}">Password Strength: {strength}</div>', unsafe_allow_html=True)
if password and confirm_password and password!=confirm_password:
    st.markdown('<div class="error-message">Passwords do not match</div>', unsafe_allow_html=True)

# --- Submit ---
if st.button("🚀 Create Account"):
    errors = {}
    if not username: errors['u']="Username required"
    if not email: errors['e']="Email required"
    if not password: errors['p']="Password required"
    if password!=confirm_password: errors['c']="Passwords do not match"
    if not agree_terms: errors['t']="Accept terms"

    if errors: 
        for e in errors.values(): st.markdown(f'<div class="error-message">{e}</div>', unsafe_allow_html=True)
    else:
        success,msg = auth_manager.register_user(username,email,password)
        if success:
            st.markdown('<div class="success-message">✅ Account created! Redirecting...</div>', unsafe_allow_html=True)
            SessionManager.login(username)
            st.switch_page("pages/Chatbot.py")  
        else:
            st.markdown(f'<div class="error-message">{msg}</div>', unsafe_allow_html=True)

# --- Login link ---
st.markdown('<div style="text-align:center;">Already have an account?</div>', unsafe_allow_html=True)
if st.button("🔑 Login"):
    st.switch_page("pages/login.py")
