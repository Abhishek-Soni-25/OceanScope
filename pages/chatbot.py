import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
from utils.query_engine import OceanDataQueryEngine
from utils.data_loader import ArgoDataLoader
from utils.auth_decorators import AuthMiddleware, require_auth
from utils.chat_manager import ChatManager
from utils.async_wrapper import run_chat_operation
from utils.session_manager import SessionManager
from utils.ui_feedback import UIFeedback, LoadingStates, ErrorMessages, SuccessMessages
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Chat - OceanScope",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up authentication for this protected page
AuthMiddleware.setup_page_auth(require_auth=True, page_name="chatbot.py", show_header=True)

# Initialize chat manager and get current user
chat_manager = ChatManager()
current_user = SessionManager.get_current_user()
user_id = current_user['id'] if current_user else None

# Initialize chat session state
if 'current_chat_session_id' not in st.session_state:
    st.session_state.current_chat_session_id = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Ensure chat_messages is always a list (defensive programming)
if not isinstance(st.session_state.chat_messages, list):
    st.session_state.chat_messages = []

# Custom CSS for better sidebar styling
st.markdown("""
<style>
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a1a;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: #2d2d2d;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize data loader and query engine with caching."""
    data_loader = ArgoDataLoader()
    query_engine = OceanDataQueryEngine()
    return data_loader, query_engine

data_loader, query_engine = init_components()

# Load data
try:
    df = data_loader.get_dataframe()
    available_profiles = data_loader.get_available_profiles()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# ===== SIDEBAR NAVIGATION =====
with st.sidebar:
    # App branding
    st.markdown("# 🌊 OceanScope")
    st.markdown("---")
    
    # User Profile Section
    if current_user:
        st.markdown("### 👤 Profile")
        st.markdown(f"**Welcome, {current_user['username']}!**")
        st.markdown(f"📧 {current_user['email']}")
        
        # Profile and Logout buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Profile", use_container_width=True):
                # You can add profile page navigation here
                st.info("Profile management coming soon!")
        with col2:
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                SessionManager.logout()
                st.switch_page("pages/landing.py")
        
        st.markdown("---")
    
    # New Chat Section
    st.markdown("### 💬 Chat")
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        # Create new chat session with proper error handling
        if user_id:
            try:
                with UIFeedback.loading_state(LoadingStates.CHAT_CREATING):
                    new_session_id, message = run_chat_operation(
                        lambda chat_mgr, uid: chat_mgr.create_chat_session(uid),
                        user_id
                    )
                
                if new_session_id:
                    st.session_state.current_chat_session_id = new_session_id
                    st.session_state.chat_messages = []
                    UIFeedback.show_success(SuccessMessages.CHAT_CREATED)
                    st.rerun()
                else:
                    UIFeedback.show_error(message)
            except Exception as e:
                UIFeedback.show_error(ErrorMessages.CHAT_CREATE_FAILED)
    
    # Chat History Section
    st.markdown("### 📜 Chat History")
    if user_id:
        try:
            chat_sessions, sessions_message = run_chat_operation(
                lambda chat_mgr, uid: chat_mgr.get_user_chat_sessions(uid),
                user_id
            )
            
            if chat_sessions:
                # Show recent chats (limit to 10 for better UI)
                recent_sessions = chat_sessions[:10]
                
                for session in recent_sessions:
                    # Format session display
                    session_name = session['session_name']
                    created_at = datetime.fromisoformat(session['created_at']).strftime("%m/%d")
                    message_count = session['message_count'] or 0
                    
                    # Highlight current session
                    is_current = st.session_state.current_chat_session_id == session['id']
                    button_type = "primary" if is_current else "secondary"
                    
                    # Truncate long session names
                    display_name = session_name[:25] + "..." if len(session_name) > 25 else session_name
                    
                    if st.button(
                        f"💬 {display_name}",
                        key=f"chat_{session['id']}", 
                        use_container_width=True,
                        type=button_type,
                        help=f"{session_name}\n{created_at} • {message_count} messages"
                    ):
                        # Load selected chat session
                        st.session_state.current_chat_session_id = session['id']
                        try:
                            messages, load_message = run_chat_operation(
                                lambda chat_mgr, sid, uid: chat_mgr.get_session_messages(sid, uid),
                                session['id'], user_id
                            )
                            st.session_state.chat_messages = messages
                            st.rerun()
                        except Exception as e:
                            UIFeedback.show_error(ErrorMessages.CHAT_LOAD_FAILED)
                            st.session_state.chat_messages = []
                
                if len(chat_sessions) > 10:
                    st.caption(f"Showing 10 of {len(chat_sessions)} chats")
            else:
                st.info("No chat history yet. Start a new chat!")
        except Exception as e:
            st.error("Could not load chat history")
    
    st.markdown("---")
    
    # Navigation Section
    st.markdown("### 🧭 Navigation")
    
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("pages/landing.py")
    
    if st.button("📊 Explore Data", use_container_width=True):
        # You can create this page later
        st.info("Data exploration page coming soon!")
    
    st.markdown("---")
    
    # Configuration Section
    st.markdown("### ⚙️ Configuration")
    
    # Profile selection for analysis
    if available_profiles:
        selected_profile = st.selectbox(
            "Ocean Profile",
            available_profiles,
            index=0,
            help="Choose which ocean profile to analyze"
        )
    else:
        st.error("No profiles available")
        st.stop()
    
    # Display options
    show_data_summary = st.checkbox("Show Data Summary", value=True)
    show_visualizations = st.checkbox("Show Plots", value=True)
    show_advanced_stats = st.checkbox("Advanced Stats", value=False)

# ===== MAIN CHAT INTERFACE =====
st.title("🤖 Chat with Argo Data")

# Ensure messages are loaded for current session
if (st.session_state.current_chat_session_id and 
    user_id and 
    not st.session_state.chat_messages):
    try:
        # Load messages if session exists but no messages in session state
        messages, load_message = run_chat_operation(
            lambda chat_mgr, sid, uid: chat_mgr.get_session_messages(sid, uid),
            st.session_state.current_chat_session_id, user_id
        )
        st.session_state.chat_messages = messages
        if messages:
            st.info(f"Loaded {len(messages)} previous messages from this chat session.")
    except Exception as e:
        st.warning(f"Could not load previous messages: {str(e)}")
    
    # Display current chat session info
    if st.session_state.current_chat_session_id:
        session_info = run_chat_operation(
            lambda chat_mgr, sid, uid: chat_mgr.get_session_info(sid, uid),
            st.session_state.current_chat_session_id, user_id
        )
        if session_info:
            st.info(f"💬 Current Chat: {session_info['session_name']} • {session_info['message_count']} messages")
    else:
        st.info("💡 Start a new chat or select from your chat history to begin!")
    
    # Display chat messages if any exist
    if st.session_state.chat_messages:
        st.markdown("### 📜 Previous Messages")
        
        for message in st.session_state.chat_messages:
            # Defensive programming: ensure message is a dictionary
            if not isinstance(message, dict):
                st.error(f"Invalid message format: {type(message)}")
                continue
                
            # Ensure required fields exist
            if 'message_type' not in message or 'content' not in message:
                st.error("Message missing required fields")
                continue
                
            if message['message_type'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
                    # Display timestamp if available
                    if 'timestamp' in message and message['timestamp']:
                        try:
                            timestamp = datetime.fromisoformat(message['timestamp']).strftime("%H:%M:%S")
                            st.caption(f"🕒 {timestamp}")
                        except (ValueError, TypeError):
                            pass  # Skip invalid timestamps
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
                    # Display timestamp if available
                    if 'timestamp' in message and message['timestamp']:
                        try:
                            timestamp = datetime.fromisoformat(message['timestamp']).strftime("%H:%M:%S")
                            st.caption(f"🕒 {timestamp}")
                        except (ValueError, TypeError):
                            pass  # Skip invalid timestamps

    st.markdown("---")
    
    # Chat input section
    st.markdown("### 💬 Ask Questions About Ocean Data")

    # Handle example selection
    default_value = ""
    if 'selected_example' in st.session_state:
        default_value = st.session_state.selected_example
        # Clear the selected example after using it
        del st.session_state.selected_example
    
    # Input query
    query = st.text_input(
        "Enter your question about the oceanographic data:",
        value=default_value,
        placeholder="e.g., What can you tell me about the temperature profile?",
        help="Ask questions about temperature, salinity, pressure, or ocean characteristics",
        key="chat_input"
    )

    # Example queries
    with st.expander("💡 Example Questions"):
        example_queries = [
            "What can you tell me about the temperature profile?",
            "How does salinity change with depth in this profile?",
            "What are the characteristics of this water mass?",
            "Is this ocean profile stratified?",
            "What's the temperature gradient in this profile?",
            "Compare the surface and deep water properties",
            "What oceanographic insights can you provide?"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"📝 {example}", key=f"example_{i}"):
                # Store the example query in a different session state key
                st.session_state.selected_example = example
                st.rerun()

    if query:
        # Ensure we have a chat session
        if not st.session_state.current_chat_session_id and user_id:
            try:
                with UIFeedback.loading_state(LoadingStates.CHAT_CREATING):
                    session_id, create_message = run_chat_operation(
                        lambda chat_mgr, uid: chat_mgr.create_chat_session(uid),
                        user_id
                    )
                
                if session_id:
                    st.session_state.current_chat_session_id = session_id
                    st.session_state.chat_messages = []  # Initialize empty message list
                    UIFeedback.show_success("Started new chat session!")
                else:
                    UIFeedback.show_error(create_message)
                    st.stop()
            except Exception as e:
                UIFeedback.show_error(ErrorMessages.CHAT_CREATE_FAILED)
                st.stop()
        
        # Save user message to database and session state
        if st.session_state.current_chat_session_id:
            try:
                with UIFeedback.loading_state(LoadingStates.CHAT_SAVING):
                    success, save_message = run_chat_operation(
                        lambda chat_mgr, sid, mtype, content, uid: chat_mgr.add_message(sid, mtype, content, uid),
                        st.session_state.current_chat_session_id, 'user', query, user_id
                    )
                
                if success:
                    # Add to session state for immediate display
                    st.session_state.chat_messages.append({
                        'message_type': 'user',
                        'content': query,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    UIFeedback.show_error(save_message)
            except Exception as e:
                UIFeedback.show_error(ErrorMessages.CHAT_SAVE_FAILED)
        
        st.write(f"🔎 **Your Question**: {query}")
        
        # Create tabs for organized display
        tab1, tab2, tab3 = st.tabs(["🤖 AI Response", "📊 Data Analysis", "📈 Visualizations"])
        
        with tab1:
            st.subheader("AI-Powered Analysis")
            
            with UIFeedback.loading_state(LoadingStates.DATA_GENERATING):
                try:
                    # Get AI response and data context
                    response_text, data_stats = query_engine.process_query(
                        query, df, selected_profile
                    )
                    
                    # Display AI response
                    st.markdown(response_text)
                    
                    # Save assistant response to database and session state
                    if st.session_state.current_chat_session_id:
                        try:
                            success, save_message = run_chat_operation(
                                lambda chat_mgr, sid, mtype, content, uid: chat_mgr.add_message(sid, mtype, content, uid),
                                st.session_state.current_chat_session_id, 'assistant', response_text, user_id
                            )
                            
                            if success:
                                # Add to session state for immediate display
                                st.session_state.chat_messages.append({
                                    'message_type': 'assistant',
                                    'content': response_text,
                                    'timestamp': datetime.now().isoformat()
                                })
                            else:
                                UIFeedback.show_warning("AI response generated but not saved to history.")
                        except Exception as e:
                            UIFeedback.show_warning("AI response generated but error saving to history.")
                    
                except Exception as e:
                    st.error(f"Error generating AI response: {str(e)}")
                    # Fallback to basic analysis using data loader
                    try:
                        profile_summary = data_loader.get_profile_summary(selected_profile)
                        if "error" not in profile_summary:
                            # Create a simple summary from profile data
                            fallback_summary = f"""
                            **Profile {selected_profile} Analysis:**
                            
                            📊 **Measurements**: {profile_summary['measurements']} data points
                            🌊 **Depth Range**: {profile_summary['depth_info']['min_pressure']:.1f} - {profile_summary['depth_info']['max_pressure']:.1f} dbar
                            
                            🌡️ **Temperature**:
                            - Surface: {profile_summary['temperature']['surface']:.2f}°C
                            - Range: {profile_summary['temperature']['min']:.2f}°C to {profile_summary['temperature']['max']:.2f}°C
                            - Average: {profile_summary['temperature']['mean']:.2f}°C
                            
                            🧂 **Salinity**:
                            - Surface: {profile_summary['salinity']['surface']:.2f} PSU
                            - Range: {profile_summary['salinity']['min']:.2f} to {profile_summary['salinity']['max']:.2f} PSU
                            - Average: {profile_summary['salinity']['mean']:.2f} PSU
                            
                            **Response to your query**: "{query}"
                            
                            The data shows typical oceanographic characteristics. For detailed AI analysis, please check your Gemini API configuration.
                            """
                            st.markdown(fallback_summary)
                            
                            # Save fallback response to database and session state
                            if st.session_state.current_chat_session_id:
                                try:
                                    success, _ = run_chat_operation(
                                        lambda chat_mgr, sid, mtype, content, uid: chat_mgr.add_message(sid, mtype, content, uid),
                                        st.session_state.current_chat_session_id, 'assistant', fallback_summary, user_id
                                    )
                                    
                                    if success:
                                        # Add to session state for immediate display
                                        st.session_state.chat_messages.append({
                                            'message_type': 'assistant',
                                            'content': fallback_summary,
                                            'timestamp': datetime.now().isoformat()
                                        })
                                except Exception as e:
                                    st.warning(f"Response generated but error saving to history: {str(e)}")
                        else:
                            error_msg = profile_summary["error"]
                            st.warning(error_msg)
                            
                            # Save error message as assistant response
                            if st.session_state.current_chat_session_id:
                                try:
                                    run_chat_operation(
                                        lambda chat_mgr, sid, mtype, content, uid: chat_mgr.add_message(sid, mtype, content, uid),
                                        st.session_state.current_chat_session_id, 'assistant', f"Error: {error_msg}", user_id
                                    )
                                except Exception:
                                    pass  # Don't show error for error message saving
                    except Exception as fallback_error:
                        error_msg = f"Unable to analyze data: {str(fallback_error)}"
                        st.error(error_msg)
                        st.info("Please check your data file and try again.")
                        
                        # Save error message as assistant response
                        if st.session_state.current_chat_session_id:
                            try:
                                success, _ = run_chat_operation(
                                    lambda chat_mgr, sid, mtype, content, uid: chat_mgr.add_message(sid, mtype, content, uid),
                                    st.session_state.current_chat_session_id, 'assistant', error_msg, user_id
                                )
                                
                                if success:
                                    # Add to session state for immediate display
                                    st.session_state.chat_messages.append({
                                        'message_type': 'assistant',
                                        'content': error_msg,
                                        'timestamp': datetime.now().isoformat()
                                    })
                            except Exception:
                                pass  # Don't show error for error message saving
        
        with tab2:
            st.subheader("Detailed Data Analysis")
            
            # Get comprehensive profile summary
            profile_summary = data_loader.get_profile_summary(selected_profile)
            
            if "error" not in profile_summary:
                # Display summary statistics
                if show_data_summary:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "📏 Measurements",
                            profile_summary["measurements"]
                        )
                        st.metric(
                            "🌡️ Surface Temp",
                            f"{profile_summary['temperature']['surface']:.2f}°C"
                        )
                    
                    with col2:
                        st.metric(
                            "🌊 Max Depth",
                            f"{profile_summary['depth_info']['max_pressure']:.1f} dbar"
                        )
                        st.metric(
                            "🧂 Surface Salinity",
                            f"{profile_summary['salinity']['surface']:.2f} PSU"
                        )
                    
                    with col3:
                        st.metric(
                            "📐 Temp Range",
                            f"{profile_summary['temperature']['max'] - profile_summary['temperature']['min']:.2f}°C"
                        )
                        st.metric(
                            "🔄 Sal Range",
                            f"{profile_summary['salinity']['max'] - profile_summary['salinity']['min']:.2f} PSU"
                        )
                
                # Advanced statistics
                if show_advanced_stats:
                    st.subheader("🔬 Advanced Analysis")
                    
                    # Water mass characteristics
                    water_chars = profile_summary["ocean_characteristics"]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Surface Layer Analysis**")
                        surface = water_chars["surface_layer"]
                        st.write(f"- Temperature: {surface['avg_temp']:.2f}°C")
                        st.write(f"- Salinity: {surface['avg_salinity']:.2f} PSU")
                        st.write(f"- Depth Range: {surface['depth_range']}")
                    
                    with col2:
                        st.write("**Deep Layer Analysis**")
                        deep = water_chars["deep_layer"]
                        st.write(f"- Temperature: {deep['avg_temp']:.2f}°C")
                        st.write(f"- Salinity: {deep['avg_salinity']:.2f} PSU")
                        st.write(f"- Depth Range: {deep['depth_range']}")
                    
                    # Stratification info
                    strat = water_chars["stratification"]
                    st.write("**Stratification Analysis**")
                    st.write(f"- Temperature Difference (Surface-Deep): {strat['temperature_difference']:.2f}°C")
                    st.write(f"- Stratification Strength: {strat['stratification_strength'].title()}")
                    st.write(f"- Is Stratified: {'Yes' if strat['is_stratified'] else 'No'}")
            else:
                st.error(profile_summary["error"])
        
        with tab3:
            if show_visualizations:
                st.subheader("Data Visualizations")
                
                # Get profile data
                df_prof = data_loader.get_profile_data(selected_profile)
                
                if not df_prof.empty:
                    # Create enhanced plots
                    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
                    
                    # Temperature profile
                    axes[0].plot(df_prof["TEMP"], df_prof["PRES"], 
                               'b-', linewidth=2, label="Temperature")
                    axes[0].invert_yaxis()
                    axes[0].set_xlabel("Temperature (°C)")
                    axes[0].set_ylabel("Pressure (dbar)")
                    axes[0].set_title(f"Temperature Profile\n(Profile {selected_profile})")
                    axes[0].grid(True, alpha=0.3)
                    
                    # Salinity profile
                    axes[1].plot(df_prof["PSAL"], df_prof["PRES"], 
                               'orange', linewidth=2, label="Salinity")
                    axes[1].invert_yaxis()
                    axes[1].set_xlabel("Salinity (PSU)")
                    axes[1].set_ylabel("Pressure (dbar)")
                    axes[1].set_title(f"Salinity Profile\n(Profile {selected_profile})")
                    axes[1].grid(True, alpha=0.3)
                    
                    # T-S diagram
                    axes[2].scatter(df_prof["PSAL"], df_prof["TEMP"], 
                                  c=df_prof["PRES"], cmap='viridis', s=30)
                    axes[2].set_xlabel("Salinity (PSU)")
                    axes[2].set_ylabel("Temperature (°C)")
                    axes[2].set_title(f"T-S Diagram\n(Color = Pressure)")
                    cbar = plt.colorbar(axes[2].collections[0], ax=axes[2])
                    cbar.set_label("Pressure (dbar)")
                    axes[2].grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Data table
                    with st.expander("📋 View Raw Data"):
                        st.dataframe(
                            df_prof[["PRES", "TEMP", "PSAL"]].round(3),
                            use_container_width=True
                        )
                else:
                    st.warning(f"No data available for profile {selected_profile}")
        
        # Note: Input will be cleared automatically on next page load

# Footer with information
st.markdown("---")
st.markdown("""
**🔧 Technical Notes:**
- AI responses powered by Google Gemini LLM (when API key is configured)
- Data analysis includes gradient calculations and water mass characteristics
- Visualizations show standard oceanographic profiles and T-S diagrams
- All data is cached for performance optimization
""")