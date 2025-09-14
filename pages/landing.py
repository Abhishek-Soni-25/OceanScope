import streamlit as st

# Configure page
st.set_page_config(
    page_title="OceanScope - AI-Powered Ocean Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session management
from utils.session_manager import SessionManager
SessionManager.initialize_session()

# Check if user is already authenticated
if SessionManager.is_authenticated():
    st.switch_page("pages/chatbot.py")

# Custom CSS for better styling with dark theme
st.markdown("""
<style>
    /* Force dark background and white text */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: #1a1a1a !important;
        color: #ffffff !important;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2a5298;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(255,255,255,0.1);
    }
    
    .feature-card h4 {
        color: #ffffff !important;
    }
    
    .feature-card p {
        color: #e0e0e0 !important;
    }
    
    .benefit-item {
        background: #1a1a1a !important;
        color: #ffffff !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #333333;
        box-shadow: 0 1px 3px rgba(255,255,255,0.1);
    }
    
    .nav-button {
        width: 100%;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: none;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .login-btn {
        background: #28a745;
        color: white;
    }
    
    .signup-btn {
        background: #007bff;
        color: white;
    }
    
    .demo-section {
        background: #1a1a1a !important;
        color: #ffffff !important;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
        border: 1px solid #333333;
    }
    
    .demo-section h3, .demo-section h4 {
        color: #ffffff !important;
    }
    
    .demo-section ul, .demo-section li {
        color: #e0e0e0 !important;
    }
    
    /* Override Streamlit's default text colors */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #ffffff !important;
    }
    
    /* Navigation section styling */
    .nav-section {
        background: #1a1a1a !important;
        color: #ffffff !important;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #333333;
    }
    
    .nav-section h4, .nav-section p {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🌊 OceanScope</h1>
    <h3>AI-Powered Ocean Data Explorer</h3>
    <p>Democratizing access to oceanographic data through intelligent analysis</p>
</div>
""", unsafe_allow_html=True)

# Project overview section
st.markdown("## 🚀 Welcome to the Future of Ocean Data Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **OceanScope** is a revolutionary platform that combines cutting-edge AI technology with comprehensive oceanographic data analysis. 
    Our platform transforms complex Argo float data into accessible insights through natural language interactions and intelligent visualizations.
    
    Whether you're a marine researcher, oceanographer, student, or simply curious about our oceans, OceanScope makes ocean data 
    exploration intuitive and powerful.
    """)

with col2:
    # Placeholder for ocean/data visualization image
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                height: 200px; 
                border-radius: 10px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: white; 
                font-size: 3rem;">
        🌊📊🤖
    </div>
    """, unsafe_allow_html=True)

# Key features section
st.markdown("## ✨ Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4>🤖 AI-Powered Analysis</h4>
        <p>Ask questions in natural language and get intelligent insights about ocean data. Our AI understands oceanographic concepts and provides detailed explanations.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Interactive Visualizations</h4>
        <p>Explore temperature and salinity profiles, T-S diagrams, and comprehensive data plots with interactive controls and customization options.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h4>💾 Persistent Chat History</h4>
        <p>Save your conversations and analysis sessions. Return to previous insights and build upon your research over time.</p>
    </div>
    """, unsafe_allow_html=True)

# Benefits section
st.markdown("## 🎯 Why Choose OceanScope?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="benefit-item">
        <strong>🔬 For Researchers:</strong> Accelerate your analysis with AI-powered insights and automated data interpretation
    </div>
    <div class="benefit-item">
        <strong>🎓 For Students:</strong> Learn oceanography through interactive exploration and intelligent explanations
    </div>
    <div class="benefit-item">
        <strong>🌍 For Educators:</strong> Demonstrate ocean concepts with real data and engaging visualizations
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="benefit-item">
        <strong>⚡ Fast & Efficient:</strong> Get instant insights without complex data processing workflows
    </div>
    <div class="benefit-item">
        <strong>🔒 Secure & Private:</strong> Your data and conversations are stored locally and kept private
    </div>
    <div class="benefit-item">
        <strong>🚀 Always Improving:</strong> Regular updates with new features and enhanced AI capabilities
    </div>
    """, unsafe_allow_html=True)

# Demo section
st.markdown("""
<div class="demo-section">
    <h3>🎬 What You Can Do</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
        <div>
            <h4>💬 Ask Natural Questions:</h4>
            <ul>
                <li>"What can you tell me about this temperature profile?"</li>
                <li>"How does salinity change with depth?"</li>
                <li>"Is this ocean profile stratified?"</li>
                <li>"Compare surface and deep water properties"</li>
            </ul>
        </div>
        <div>
            <h4>📈 Explore Data Visually:</h4>
            <ul>
                <li>Interactive temperature and salinity profiles</li>
                <li>Temperature-Salinity (T-S) diagrams</li>
                <li>Water mass analysis and characteristics</li>
                <li>Stratification and gradient calculations</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation section
st.markdown("## 🚪 Get Started")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div class="nav-section" style="text-align: center;">
        <h4>Ready to explore ocean data?</h4>
        <p>Join thousands of researchers and students already using OceanScope</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col_login, col_signup = st.columns(2)
    
    with col_login:
        if st.button("🔑 Login", key="login_btn", help="Sign in to your existing account"):
            st.switch_page("pages/login.py")
    
    with col_signup:
        if st.button("📝 Sign Up", key="signup_btn", help="Create a new account"):
            st.switch_page("pages/signup.py")

# Technical specifications
with st.expander("🔧 Technical Specifications"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Sources:**
        - Argo Float Network data
        - NetCDF format support
        - Real-time oceanographic measurements
        
        **AI Technology:**
        - Google Gemini LLM integration
        - Natural language processing
        - Context-aware responses
        """)
    
    with col2:
        st.markdown("""
        **Features:**
        - SQLite database for local storage
        - Secure user authentication
        - Session management
        - Responsive web interface
        
        **Supported Analysis:**
        - Water mass characterization
        - Stratification analysis
        - Temperature/Salinity profiling
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>🌊 <strong>OceanScope</strong> - Making ocean data accessible to everyone</p>
    <p>Built with ❤️ using Streamlit, Python, and AI</p>
</div>
""", unsafe_allow_html=True)