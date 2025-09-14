import streamlit as st
from utils.session_manager import SessionManager
from utils.auth_decorators import AuthMiddleware

# Configure page
st.set_page_config(
    page_title="OceanScope - AI-Powered Ocean Data Explorer",
    page_icon="🌊",
    layout="wide"
)

# Initialize authentication middleware
AuthMiddleware.initialize()

# Check authentication status and route accordingly
if SessionManager.is_authenticated():
    # User is authenticated, redirect to main chat interface
    st.switch_page("pages/chatbot.py")
else:
    # User is not authenticated, redirect to landing page
    st.switch_page("pages/landing.py")
