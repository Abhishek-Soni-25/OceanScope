import streamlit as st
from utils.auth_manager import AuthManager
from utils.session_manager import SessionManager

# --- Page config ---
st.set_page_config(page_title="Login - OceanScope", page_icon="🔑", layout="centered")

# --- Dark theme CSS ---
st.markdown("""
<style>
.stApp { background-color:#000;color:#fff; }
.login-container { max-width:400px;margin:2rem auto;padding:2rem;background:#1a1a1a;border-radius:10px;box-shadow:0 4px 6px rgba(255,255,255,0.1);border:1px solid #333; }
.stTextInput > div > div > input { background:#2d2d2d;color:#fff;border:1px solid #555; }
.stButton > button { background:#2d2d2d;color:#fff;border:1px solid #555; }
.error-message { color:#ff6b6b;background:#2d1b1b;padding:0.5rem;border-radius:5px;border-left:4px solid #ff6b6b;margin:0.5rem 0; }
.success-message { color:#51cf66;background:#1b2d1b;padding:0.5rem;border-radius:5px;border-left:4px solid #51cf66;margin:0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# --- Initialize ---
auth_manager = AuthManager()
SessionManager.initialize_session()

# Redirect if already logged in
if SessionManager.is_authenticated():
    st.switch_page("pages/Chatbot.py")  

st.markdown('<div class="login-container"><h3 style="text-align:center;">Login to OceanScope</h3></div>', unsafe_allow_html=True)

# --- Form fields ---
username = st.text_input("Username", placeholder="Enter your username")
password = st.text_input("Password", type="password", placeholder="Enter your password")
remember_me = st.checkbox("Remember me") 

# --- Login button ---
if st.button("🔑 Login"):
    if not username or not password:
        st.markdown('<div class="error-message">Username and password are required</div>', unsafe_allow_html=True)
    else:
        success, message = auth_manager.login_user(username, password)
        if success:
            SessionManager.login(username)
            st.markdown('<div class="success-message">✅ Login successful! Redirecting...</div>', unsafe_allow_html=True)
            st.switch_page("pages/Chatbot.py")  
        else:
            st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)

# --- Links ---
st.markdown('<div style="text-align:center;">New here? Create an account below</div>', unsafe_allow_html=True)
if st.button("📝 Sign Up"):
    st.switch_page("pages/signup.py") 
