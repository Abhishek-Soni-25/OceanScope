"""
Authentication Manager for handling user registration, login, and password management.
Updated to use PostgreSQL instead of SQLite.
"""
import bcrypt
import logging
import asyncio
from typing import Optional, Dict, Tuple
from datetime import datetime
import uuid

from database.postgresql_manager import get_database_manager, DatabaseError
from utils.session_manager import SessionManager


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class AuthManager:
    """Manages user authentication operations with PostgreSQL."""
    
    def __init__(self):
        """Initialize authentication manager."""
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
    
    async def register_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        first_name: str = None,
        last_name: str = None
    ) -> Tuple[bool, str]:
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
            
            # Get database manager
            db_manager = await get_database_manager()
            
            # Check if username already exists
            try:
                existing_user = await db_manager.get_user_by_username(username)
                if existing_user:
                    return False, "Username already exists. Please choose a different username."
            except DatabaseError as e:
                self.logger.error(f"Error checking username availability: {e}")
                return False, "Unable to verify username availability. Please try again."
            
            # Check if email already exists
            try:
                existing_user = await db_manager.get_user_by_email(email)
                if existing_user:
                    return False, "Email already registered. Please use a different email or try logging in."
            except DatabaseError as e:
                self.logger.error(f"Error checking email availability: {e}")
                return False, "Unable to verify email availability. Please try again."
            
            # Hash password and create user
            try:
                password_hash = self.hash_password(password)
                
                user_id = await db_manager.create_user(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    first_name=first_name,
                    last_name=last_name
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
    
    async def authenticate_user(self, username: str, password: str) -> Tuple[Optional[Dict], str]:
        """Authenticate user with username and password with detailed error reporting."""
        try:
            # Input validation
            if not username or not isinstance(username, str):
                return None, "Username or email is required"
            if not password or not isinstance(password, str):
                return None, "Password is required"
            
            # Clean inputs
            username = username.strip()
            
            # Get database manager
            db_manager = await get_database_manager()
            
            # Get user by username or email
            user = None
            try:
                user = await db_manager.get_user_by_username(username)
                if not user:
                    user = await db_manager.get_user_by_email(username)
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
                await db_manager.update_user_last_login(user['id'])
            except DatabaseError as e:
                self.logger.warning(f"Failed to update last login for user {user['id']}: {e}")
                # Don't fail authentication for this
            
            # Return user data without password hash
            user_data = {
                'id': str(user['id']),  # Convert UUID to string for JSON serialization
                'username': user['username'],
                'email': user['email'],
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'role': user.get('role', 'user'),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': datetime.now().isoformat()
            }
            
            self.logger.info(f"User authenticated successfully: {username}")
            return user_data, "Login successful!"
            
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return None, "An unexpected error occurred. Please try again."
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID without password hash."""
        try:
            db_manager = await get_database_manager()
            user = await db_manager.get_user_by_id(user_id)
            
            if user:
                # Remove password hash from returned data
                user_data = dict(user)
                user_data.pop('password_hash', None)
                user_data['id'] = str(user_data['id'])  # Convert UUID to string
                return user_data
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {e}")
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
    
    async def login_user_with_session(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user and create session with detailed feedback."""
        try:
            user_data, message = await self.authenticate_user(username, password)
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
    
    async def update_user_profile(
        self, 
        user_id: str, 
        first_name: str = None, 
        last_name: str = None,
        bio: str = None,
        organization: str = None,
        research_interests: list = None,
        location: str = None,
        website: str = None
    ) -> Tuple[bool, str]:
        """Update user profile information."""
        try:
            db_manager = await get_database_manager()
            
            # Update users table
            update_fields = []
            params = []
            param_count = 1
            
            if first_name is not None:
                update_fields.append(f"first_name = ${param_count}")
                params.append(first_name)
                param_count += 1
            
            if last_name is not None:
                update_fields.append(f"last_name = ${param_count}")
                params.append(last_name)
                param_count += 1
            
            if update_fields:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ${param_count}"
                await db_manager.execute_query(query, tuple(params))
            
            # Update user_profiles table
            profile_fields = []
            profile_params = []
            profile_param_count = 1
            
            if bio is not None:
                profile_fields.append(f"bio = ${profile_param_count}")
                profile_params.append(bio)
                profile_param_count += 1
            
            if organization is not None:
                profile_fields.append(f"organization = ${profile_param_count}")
                profile_params.append(organization)
                profile_param_count += 1
            
            if research_interests is not None:
                profile_fields.append(f"research_interests = ${profile_param_count}")
                profile_params.append(research_interests)
                profile_param_count += 1
            
            if location is not None:
                profile_fields.append(f"location = ${profile_param_count}")
                profile_params.append(location)
                profile_param_count += 1
            
            if website is not None:
                profile_fields.append(f"website = ${profile_param_count}")
                profile_params.append(website)
                profile_param_count += 1
            
            if profile_fields:
                profile_params.append(user_id)
                profile_query = f"UPDATE user_profiles SET {', '.join(profile_fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ${profile_param_count}"
                await db_manager.execute_query(profile_query, tuple(profile_params))
            
            self.logger.info(f"User profile updated successfully: {user_id}")
            return True, "Profile updated successfully!"
            
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            return False, "Failed to update profile. Please try again."
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password."""
        try:
            # Validate new password strength
            is_strong, strength_message = self.validate_password_strength(new_password)
            if not is_strong:
                return False, strength_message
            
            # Get current user
            db_manager = await get_database_manager()
            user = await db_manager.get_user_by_id(user_id)
            
            if not user:
                return False, "User not found"
            
            # Verify old password
            if not self.verify_password(old_password, user['password_hash']):
                return False, "Current password is incorrect"
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            await db_manager.execute_query(
                "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                (new_password_hash, user_id)
            )
            
            self.logger.info(f"Password changed successfully for user: {user_id}")
            return True, "Password changed successfully!"
            
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            return False, "Failed to change password. Please try again."