"""
Chat Manager for handling chat sessions and message persistence.
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .database_manager import DatabaseManager, DatabaseError


class ChatError(Exception):
    """Custom exception for chat-related errors."""
    pass


class ChatManager:
    """Manages chat sessions and messages with database persistence."""
    
    def __init__(self, db_path: str = "app_data.db"):
        """Initialize chat manager with database connection."""
        self.db_manager = DatabaseManager(db_path)
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def create_chat_session(self, user_id: int, session_name: str = None) -> Tuple[Optional[int], str]:
        """
        Create a new chat session for a user with error handling.
        
        Args:
            user_id: ID of the user creating the session
            session_name: Optional name for the session (auto-generated if None)
            
        Returns:
            Tuple of (session_id, message)
        """
        try:
            # Input validation
            if not isinstance(user_id, int) or user_id <= 0:
                return None, "Invalid user ID"
            
            # Check database availability
            if not self.db_manager.check_availability():
                return None, "Chat service temporarily unavailable. Please try again later."
            
            if session_name is None:
                # Auto-generate session name with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                session_name = f"Chat {timestamp}"
            
            # Validate session name
            if session_name and len(session_name.strip()) > 100:
                session_name = session_name.strip()[:100]
            
            session_id = self.db_manager.execute_query(
                """INSERT INTO chat_sessions (user_id, session_name, created_at, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (user_id, session_name.strip() if session_name else None)
            )
            
            if session_id:
                self.logger.info(f"Chat session created successfully: {session_id} for user {user_id}")
                return session_id, "New chat session created successfully!"
            else:
                return None, "Failed to create chat session. Please try again."
                
        except DatabaseError as e:
            self.logger.error(f"Database error creating chat session: {e}")
            return None, "Unable to create chat session. Please try again later."
        except Exception as e:
            self.logger.error(f"Unexpected error creating chat session: {e}")
            return None, "An unexpected error occurred. Please try again."
    
    def get_user_chat_sessions(self, user_id: int) -> Tuple[List[Dict], str]:
        """
        Get all chat sessions for a user, ordered by most recent first.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple of (sessions_list, message)
        """
        try:
            # Input validation
            if not isinstance(user_id, int) or user_id <= 0:
                return [], "Invalid user ID"
            
            # Check database availability
            if not self.db_manager.check_availability():
                return [], "Chat history temporarily unavailable. Please try again later."
            
            sessions = self.db_manager.execute_query(
                """SELECT cs.*, 
                          COUNT(cm.id) as message_count,
                          MAX(cm.timestamp) as last_message_time
                   FROM chat_sessions cs
                   LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                   WHERE cs.user_id = ?
                   GROUP BY cs.id
                   ORDER BY cs.updated_at DESC""",
                (user_id,)
            )
            
            session_list = [dict(session) for session in sessions]
            self.logger.debug(f"Retrieved {len(session_list)} chat sessions for user {user_id}")
            
            if session_list:
                return session_list, f"Found {len(session_list)} chat sessions"
            else:
                return [], "No chat history found"
                
        except DatabaseError as e:
            self.logger.error(f"Database error retrieving chat sessions: {e}")
            return [], "Unable to load chat history. Please try again later."
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving chat sessions: {e}")
            return [], "An unexpected error occurred loading chat history."
    
    def get_session_messages(self, session_id: int, user_id: int = None) -> Tuple[List[Dict], str]:
        """
        Get all messages for a specific chat session with error handling.
        
        Args:
            session_id: ID of the chat session
            user_id: Optional user ID for additional security check
            
        Returns:
            Tuple of (messages_list, message)
        """
        try:
            # Input validation
            if not isinstance(session_id, int) or session_id <= 0:
                return [], "Invalid session ID"
            
            # Check database availability
            if not self.db_manager.check_availability():
                return [], "Chat messages temporarily unavailable. Please try again later."
            
            # If user_id is provided, verify the session belongs to the user
            if user_id is not None:
                try:
                    session_check = self.db_manager.execute_query(
                        "SELECT user_id FROM chat_sessions WHERE id = ?",
                        (session_id,)
                    )
                    if not session_check or session_check[0]['user_id'] != user_id:
                        return [], "Unauthorized access to chat session"
                except DatabaseError as e:
                    self.logger.error(f"Error verifying session ownership: {e}")
                    return [], "Unable to verify session access. Please try again."
            
            messages = self.db_manager.execute_query(
                """SELECT * FROM chat_messages 
                   WHERE session_id = ? 
                   ORDER BY timestamp ASC""",
                (session_id,)
            )
            
            message_list = [dict(message) for message in messages]
            self.logger.debug(f"Retrieved {len(message_list)} messages for session {session_id}")
            
            if message_list:
                return message_list, f"Loaded {len(message_list)} messages"
            else:
                return [], "No messages found in this session"
                
        except DatabaseError as e:
            self.logger.error(f"Database error retrieving messages: {e}")
            return [], "Unable to load messages. Please try again later."
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving messages: {e}")
            return [], "An unexpected error occurred loading messages."
    
    def add_message(self, session_id: int, message_type: str, content: str, user_id: int = None) -> Tuple[bool, str]:
        """
        Add a message to a chat session with comprehensive error handling.
        
        Args:
            session_id: ID of the chat session
            message_type: Type of message ('user' or 'assistant')
            content: Message content
            user_id: Optional user ID for security check
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Input validation
            if not isinstance(session_id, int) or session_id <= 0:
                return False, "Invalid session ID"
            
            if message_type not in ['user', 'assistant']:
                return False, "Invalid message type"
            
            if not content or not isinstance(content, str):
                return False, "Message content cannot be empty"
            
            # Limit message length
            if len(content) > 10000:  # 10KB limit
                content = content[:10000] + "... [message truncated]"
            
            # Check database availability
            if not self.db_manager.check_availability():
                return False, "Chat service temporarily unavailable. Please try again later."
            
            # If user_id is provided, verify the session belongs to the user
            if user_id is not None:
                try:
                    session_check = self.db_manager.execute_query(
                        "SELECT user_id FROM chat_sessions WHERE id = ?",
                        (session_id,)
                    )
                    if not session_check or session_check[0]['user_id'] != user_id:
                        return False, "Unauthorized access to chat session"
                except DatabaseError as e:
                    self.logger.error(f"Error verifying session ownership: {e}")
                    return False, "Unable to verify session access. Please try again."
            
            # Add the message
            try:
                message_id = self.db_manager.execute_query(
                    """INSERT INTO chat_messages (session_id, message_type, content, timestamp) 
                       VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                    (session_id, message_type, content.strip())
                )
                
                if not message_id:
                    return False, "Failed to save message. Please try again."
                
                # Update the session's updated_at timestamp
                self.db_manager.execute_query(
                    "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (session_id,)
                )
                
                self.logger.debug(f"Message added successfully to session {session_id}")
                return True, "Message saved successfully"
                
            except DatabaseError as e:
                self.logger.error(f"Database error adding message: {e}")
                return False, "Unable to save message. Please try again later."
            
        except Exception as e:
            self.logger.error(f"Unexpected error adding message: {e}")
            return False, "An unexpected error occurred. Please try again."
    
    def update_session_name(self, session_id: int, new_name: str, user_id: int = None) -> bool:
        """
        Update the name of a chat session.
        
        Args:
            session_id: ID of the chat session
            new_name: New name for the session
            user_id: Optional user ID for security check
            
        Returns:
            True if session name was updated successfully, False otherwise
        """
        # If user_id is provided, verify the session belongs to the user
        if user_id is not None:
            session_check = self.db_manager.execute_query(
                "SELECT user_id FROM chat_sessions WHERE id = ?",
                (session_id,)
            )
            if not session_check or session_check[0]['user_id'] != user_id:
                return False
        
        try:
            rows_affected = self.db_manager.execute_query(
                """UPDATE chat_sessions 
                   SET session_name = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (new_name, session_id)
            )
            return rows_affected > 0
        except Exception:
            return False
    
    def delete_chat_session(self, session_id: int, user_id: int = None) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            session_id: ID of the chat session to delete
            user_id: Optional user ID for security check
            
        Returns:
            True if session was deleted successfully, False otherwise
        """
        # If user_id is provided, verify the session belongs to the user
        if user_id is not None:
            session_check = self.db_manager.execute_query(
                "SELECT user_id FROM chat_sessions WHERE id = ?",
                (session_id,)
            )
            if not session_check or session_check[0]['user_id'] != user_id:
                return False
        
        try:
            # Delete all messages in the session first (due to foreign key constraint)
            self.db_manager.execute_query(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,)
            )
            
            # Delete the session
            rows_affected = self.db_manager.execute_query(
                "DELETE FROM chat_sessions WHERE id = ?",
                (session_id,)
            )
            
            return rows_affected > 0
        except Exception:
            return False
    
    def get_session_info(self, session_id: int, user_id: int = None) -> Optional[Dict]:
        """
        Get information about a specific chat session.
        
        Args:
            session_id: ID of the chat session
            user_id: Optional user ID for security check
            
        Returns:
            Dictionary with session information or None if not found/unauthorized
        """
        # If user_id is provided, verify the session belongs to the user
        if user_id is not None:
            session_info = self.db_manager.execute_query(
                """SELECT cs.*, COUNT(cm.id) as message_count
                   FROM chat_sessions cs
                   LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                   WHERE cs.id = ? AND cs.user_id = ?
                   GROUP BY cs.id""",
                (session_id, user_id)
            )
        else:
            session_info = self.db_manager.execute_query(
                """SELECT cs.*, COUNT(cm.id) as message_count
                   FROM chat_sessions cs
                   LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                   WHERE cs.id = ?
                   GROUP BY cs.id""",
                (session_id,)
            )
        
        return dict(session_info[0]) if session_info else None
    
    def get_user_message_count(self, user_id: int) -> int:
        """
        Get total number of messages for a user across all sessions.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Total message count
        """
        result = self.db_manager.execute_query(
            """SELECT COUNT(cm.id) as total_messages
               FROM chat_messages cm
               JOIN chat_sessions cs ON cm.session_id = cs.id
               WHERE cs.user_id = ?""",
            (user_id,)
        )
        
        return result[0]['total_messages'] if result else 0