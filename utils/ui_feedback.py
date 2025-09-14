"""
UI Feedback utilities for providing user-friendly messages and loading states.
"""
import streamlit as st
import time
from contextlib import contextmanager
from typing import Optional, Any, Callable


class UIFeedback:
    """Utility class for consistent user feedback across the application."""
    
    @staticmethod
    def show_error(message: str, details: str = None):
        """Display an error message with optional details."""
        st.error(f"❌ {message}")
        if details:
            with st.expander("Error Details"):
                st.text(details)
    
    @staticmethod
    def show_success(message: str):
        """Display a success message."""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """Display a warning message."""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info(message: str):
        """Display an info message."""
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def show_loading(message: str = "Loading..."):
        """Display a loading message."""
        return st.spinner(f"🔄 {message}")
    
    @staticmethod
    @contextmanager
    def loading_state(message: str = "Processing...", success_message: str = None):
        """Context manager for loading states with optional success message."""
        with st.spinner(f"🔄 {message}"):
            try:
                yield
                if success_message:
                    st.success(f"✅ {success_message}")
            except Exception as e:
                st.error(f"❌ Operation failed: {str(e)}")
                raise
    
    @staticmethod
    def show_database_error():
        """Display a standard database error message."""
        st.error("❌ Database temporarily unavailable. Please try again in a few moments.")
        st.info("💡 If the problem persists, please contact support.")
    
    @staticmethod
    def show_network_error():
        """Display a standard network error message."""
        st.error("❌ Network connection issue. Please check your internet connection.")
        st.info("💡 Try refreshing the page or try again later.")
    
    @staticmethod
    def show_validation_errors(errors: dict):
        """Display validation errors in a consistent format."""
        if errors:
            st.error("❌ Please fix the following issues:")
            for field, error in errors.items():
                st.markdown(f"• **{field.title()}**: {error}")
    
    @staticmethod
    def show_form_feedback(success: bool, message: str, field_errors: dict = None):
        """Display comprehensive form feedback."""
        if success:
            UIFeedback.show_success(message)
        else:
            UIFeedback.show_error(message)
            if field_errors:
                UIFeedback.show_validation_errors(field_errors)
    
    @staticmethod
    def confirm_action(message: str, key: str = None) -> bool:
        """Show a confirmation dialog for destructive actions."""
        return st.button(f"⚠️ {message}", key=key, type="secondary")
    
    @staticmethod
    def show_progress(current: int, total: int, message: str = "Progress"):
        """Display a progress bar with message."""
        progress = current / total if total > 0 else 0
        st.progress(progress, text=f"{message}: {current}/{total}")
    
    @staticmethod
    def show_retry_option(error_message: str, retry_callback: Callable, retry_key: str = "retry"):
        """Show error with retry option."""
        st.error(f"❌ {error_message}")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Retry", key=retry_key):
                retry_callback()
        with col2:
            st.info("💡 If the problem persists, try refreshing the page.")


class LoadingStates:
    """Predefined loading states for common operations."""
    
    AUTH_LOGIN = "Authenticating user..."
    AUTH_REGISTER = "Creating your account..."
    AUTH_LOGOUT = "Logging out..."
    
    CHAT_CREATING = "Creating new chat session..."
    CHAT_LOADING = "Loading chat history..."
    CHAT_SAVING = "Saving message..."
    CHAT_DELETING = "Deleting chat session..."
    
    DATA_LOADING = "Loading ocean data..."
    DATA_ANALYZING = "Analyzing data..."
    DATA_GENERATING = "Generating AI response..."
    
    DB_CONNECTING = "Connecting to database..."
    DB_SAVING = "Saving to database..."
    DB_RETRIEVING = "Retrieving data..."


class ErrorMessages:
    """Predefined error messages for consistency."""
    
    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "Invalid username/email or password"
    AUTH_USER_EXISTS = "Username or email already exists"
    AUTH_WEAK_PASSWORD = "Password does not meet security requirements"
    AUTH_REQUIRED_FIELD = "This field is required"
    AUTH_SESSION_EXPIRED = "Your session has expired. Please log in again."
    
    # Database errors
    DB_UNAVAILABLE = "Service temporarily unavailable. Please try again later."
    DB_CONNECTION_FAILED = "Unable to connect to database"
    DB_SAVE_FAILED = "Failed to save data. Please try again."
    DB_RETRIEVE_FAILED = "Failed to retrieve data. Please try again."
    
    # Chat errors
    CHAT_CREATE_FAILED = "Failed to create chat session"
    CHAT_LOAD_FAILED = "Failed to load chat history"
    CHAT_SAVE_FAILED = "Failed to save message"
    CHAT_UNAUTHORIZED = "Unauthorized access to chat session"
    
    # General errors
    UNEXPECTED_ERROR = "An unexpected error occurred. Please try again."
    NETWORK_ERROR = "Network connection issue. Please check your internet connection."
    VALIDATION_ERROR = "Please fix the validation errors below"


class SuccessMessages:
    """Predefined success messages for consistency."""
    
    # Authentication
    AUTH_LOGIN_SUCCESS = "Login successful! Welcome back."
    AUTH_REGISTER_SUCCESS = "Account created successfully! Welcome to OceanScope."
    AUTH_LOGOUT_SUCCESS = "You have been logged out successfully."
    
    # Chat
    CHAT_CREATED = "New chat session created successfully!"
    CHAT_MESSAGE_SAVED = "Message saved to chat history"
    CHAT_LOADED = "Chat history loaded successfully"
    CHAT_DELETED = "Chat session deleted successfully"
    
    # Data
    DATA_LOADED = "Ocean data loaded successfully"
    DATA_ANALYZED = "Data analysis completed"
    
    # General
    OPERATION_SUCCESS = "Operation completed successfully"
    SAVE_SUCCESS = "Data saved successfully"


# Convenience functions for common patterns
def with_error_handling(func: Callable, error_message: str = None, show_details: bool = False):
    """Decorator-like function to wrap operations with error handling."""
    try:
        return func()
    except Exception as e:
        error_msg = error_message or ErrorMessages.UNEXPECTED_ERROR
        if show_details:
            UIFeedback.show_error(error_msg, str(e))
        else:
            UIFeedback.show_error(error_msg)
        return None


def safe_operation(operation: Callable, loading_message: str, success_message: str = None, error_message: str = None):
    """Safely execute an operation with loading state and error handling."""
    try:
        with UIFeedback.loading_state(loading_message, success_message):
            return operation()
    except Exception as e:
        error_msg = error_message or ErrorMessages.UNEXPECTED_ERROR
        UIFeedback.show_error(error_msg)
        return None