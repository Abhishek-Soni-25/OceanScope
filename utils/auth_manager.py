"""
Authentication Manager for handling user registration, login, and password management.
"""
import bcrypt
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime
from .database_manager import DatabaseManager, DatabaseError
from .session_manager import SessionManager


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class AuthManager:
    """Manages user authentication operations."""
    
    def __init__(self, db_path: str = "app_data.db"):
        """Initialize authentication manager with database."""
        self.db_manager = DatabaseManager(db_path)
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with error handling."""
        try:
            if not password or not isinstance(password, str):
                raise AuthenticationError("Password cannot be empty")
                
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Password hashing failed: {e}")
            raise AuthenticationError("Failed to secure password")
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash with error handling."""
        try:
            if not password or not password_hash:
                return False
                
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """Register a new user with detailed error reporting."""
        try:
            # Input validation
            if not username or not isinstance(username, str):
                return False, "Username is required"
            if not email or not isinstance(email, str):
                return False, "Email is required"
            if not password or not isinstance(password, str):
                return False, "Password is required"
            
            # Clean inputs
            username = username.strip()
            email = email.strip().lower()
            
            # Validate password strength
            is_strong, strength_message = self.validate_password_strength(password)
            if not is_strong:
                return False, strength_message
            
            # Check database availability
            if not self.db_manager.check_availability():
                return False, "Service temporarily unavailable. Please try again later."
            
            # Check if username already exists
            try:
                if self.db_manager.get_user_by_username(username):
                    return False, "Username already exists. Please choose a different username."
            except DatabaseError as e:
                self.logger.error(f"Error checking username availability: {e}")
                return False, "Unable to verify username availability. Please try again."
            
            # Check if email already exists
            try:
                if self.db_manager.get_user_by_email(email):
                    return False, "Email already registered. Please use a different email or try logging in."
            except DatabaseError as e:
                self.logger.error(f"Error checking email availability: {e}")
                return False, "Unable to verify email availability. Please try again."
            
            # Hash password and create user
            try:
                password_hash = self.hash_password(password)
                
                user_id = self.db_manager.execute_query(
                    """INSERT INTO users (username, email, password_hash) 
                       VALUES (?, ?, ?)""",
                    (username, email, password_hash)
                )
                
                if user_id:
                    self.logger.info(f"User registered successfully: {username}")
                    return True, "Account created successfully!"
                else:
                    return False, "Failed to create account. Please try again."
                    
            except DatabaseError as e:
                self.logger.error(f"Database error during registration: {e}")
                if "already exists" in str(e).lower():
                    return False, "Username or email already exists. Please choose different credentials."
                else:
                    return False, "Unable to create account. Please try again later."
            
        except AuthenticationError as e:
            return False, str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error during registration: {e}")
            return False, "An unexpected error occurred. Please try again."
    
    def authenticate_user(self, username: str, password: str) -> Tuple[Optional[Dict], str]:
        """Authenticate user with username and password with detailed error reporting."""
        try:
            # Input validation
            if not username or not isinstance(username, str):
                return None, "Username or email is required"
            if not password or not isinstance(password, str):
                return None, "Password is required"
            
            # Clean inputs
            username = username.strip()
            
            # Check database availability
            if not self.db_manager.check_availability():
                return None, "Service temporarily unavailable. Please try again later."
            
            # Get user by username or email
            user = None
            try:
                user = self.db_manager.get_user_by_username(username)
                if not user:
                    user = self.db_manager.get_user_by_email(username)
            except DatabaseError as e:
                self.logger.error(f"Database error during authentication: {e}")
                return None, "Unable to verify credentials. Please try again later."
            
            if not user:
                self.logger.warning(f"Authentication failed: user not found for {username}")
                return None, "Invalid username/email or password"
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                self.logger.warning(f"Authentication failed: invalid password for {username}")
                return None, "Invalid username/email or password"
            
            # Update last login
            try:
                self.db_manager.execute_query(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user['id'],)
                )
            except DatabaseError as e:
                self.logger.warning(f"Failed to update last login for user {user['id']}: {e}")
                # Don't fail authentication for this
            
            # Return user data without password hash
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'],
                'last_login': datetime.now().isoformat()
            }
            
            self.logger.info(f"User authenticated successfully: {username}")
            return user_data, "Login successful!"
            
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return None, "An unexpected error occurred. Please try again."
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID without password hash."""
        user = self.db_manager.get_user_by_id(user_id)
        if user:
            # Remove password hash from returned data
            user_data = dict(user)
            user_data.pop('password_hash', None)
            return user_data
        return None
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        return True, "Password is strong"
    
    def login_user_with_session(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user and create session with detailed feedback."""
        try:
            user_data, message = self.authenticate_user(username, password)
            if user_data:
                SessionManager.login_user(user_data)
                return True, message
            else:
                return False, message
        except Exception as e:
            self.logger.error(f"Error during session login: {e}")
            return False, "Login failed due to system error. Please try again."
    
    def logout_user_with_session(self) -> None:
        """Logout user and clear session."""
        SessionManager.logout_user()
    
    def is_user_authenticated(self) -> bool:
        """Check if user is authenticated via session."""
        return SessionManager.validate_session()
    
    def get_current_user_data(self) -> Optional[Dict]:
        """Get current authenticated user data."""
        return SessionManager.get_current_user()
    
    def require_authentication(self) -> bool:
        """Require authentication for protected pages."""
        return SessionManager.require_authentication()