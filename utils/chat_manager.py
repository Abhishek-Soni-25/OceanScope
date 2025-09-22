"""
Chat Manager for handling chat sessions and message persistence.
Updated to use PostgreSQL instead of SQLite.
"""
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

from database.postgresql_manager import get_database_manager, DatabaseError


class ChatError(Exception):
    """Custom exception for chat-related errors."""
    pass


class ChatManager:
    """Manages chat sessions and messages with PostgreSQL persistence."""
    
    def __init__(self):
        """Initialize chat manager."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def create_chat_session(
        self, 
        user_id: str, 
        session_name: str = None,
        description: str = None
    ) -> Tuple[Optional[str], str]:
        """
        Create a new chat session for a user with error handling.
        
        Args:
            user_id: ID of the user creating the session
            session_name: Optional name for the session (auto-generated if None)
            description: Optional description for the session
            
        Returns:
            Tuple of (session_id, message)
        """
        try:
            # Input validation
            if not user_id or not isinstance(user_id, str):
                return None, "Invalid user ID"
            
            # Get database manager
            db_manager = await get_database_manager()
            
            if session_name is None:
                # Auto-generate session name with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                session_name = f"Chat {timestamp}"
            
            # Validate session name
            if session_name and len(session_name.strip()) > 100:
                session_name = session_name.strip()[:100]
            
            session_id = await db_manager.create_chat_session(
                user_id=user_id,
                session_name=session_name.strip() if session_name else None,
                description=description
            )
            
            if session_id:
                self.logger.info(f"Chat session created successfully: {session_id} for user {user_id}")
                return str(session_id), "New chat session created successfully!"
            else:
                return None, "Failed to create chat session. Please try again."
                
        except DatabaseError as e:
            self.logger.error(f"Database error creating chat session: {e}")
            return None, "Unable to create chat session. Please try again later."
        except Exception as e:
            self.logger.error(f"Unexpected error creating chat session: {e}")
            return None, "An unexpected error occurred. Please try again."
    
    async def get_user_chat_sessions(self, user_id: str) -> Tuple[List[Dict], str]:
        """
        Get all chat sessions for a user, ordered by most recent first.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple of (sessions_list, message)
        """
        try:
            # Input validation
            if not user_id or not isinstance(user_id, str):
                return [], "Invalid user ID"
            
            # Get database manager
            db_manager = await get_database_manager()
            
            sessions = await db_manager.get_user_chat_sessions(user_id)
            
            # Convert UUIDs to strings for JSON serialization
            session_list = []
            for session in sessions:
                session_dict = dict(session)
                session_dict['id'] = str(session_dict['id'])
                session_dict['user_id'] = str(session_dict['user_id'])
                session_list.append(session_dict)
            
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
    
    async def get_session_messages(
        self, 
        session_id: str, 
        user_id: str = None
    ) -> Tuple[List[Dict], str]:
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
            if not session_id or not isinstance(session_id, str):
                return [], "Invalid session ID"
            
            # Get database manager
            db_manager = await get_database_manager()
            
            messages = await db_manager.get_chat_messages(session_id, user_id)
            
            # Convert UUIDs to strings for JSON serialization
            message_list = []
            for message in messages:
                message_dict = dict(message)
                message_dict['id'] = str(message_dict['id'])
                message_dict['session_id'] = str(message_dict['session_id'])
                message_list.append(message_dict)
            
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
    
    async def add_message(
        self, 
        session_id: str, 
        message_type: str, 
        content: str, 
        user_id: str = None,
        metadata: Dict = None
    ) -> Tuple[bool, str]:
        """
        Add a message to a chat session with comprehensive error handling.
        
        Args:
            session_id: ID of the chat session
            message_type: Type of message ('user' or 'assistant')
            content: Message content
            user_id: Optional user ID for security check
            metadata: Optional metadata for the message
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Input validation
            if not session_id or not isinstance(session_id, str):
                return False, "Invalid session ID"
            
            if message_type not in ['user', 'assistant']:
                return False, "Invalid message type"
            
            if not content or not isinstance(content, str):
                return False, "Message content cannot be empty"
            
            # Limit message length
            if len(content) > 10000:  # 10KB limit
                content = content[:10000] + "... [message truncated]"
            
            # Get database manager
            db_manager = await get_database_manager()
            
            # Add the message
            try:
                message_id = await db_manager.add_chat_message(
                    session_id=session_id,
                    message_type=message_type,
                    content=content.strip(),
                    user_id=user_id,
                    metadata=metadata
                )
                
                if message_id:
                    self.logger.debug(f"Message added successfully to session {session_id}")
                    return True, "Message saved successfully"
                else:
                    return False, "Failed to save message. Please try again."
                
            except DatabaseError as e:
                self.logger.error(f"Database error adding message: {e}")
                return False, "Unable to save message. Please try again later."
            
        except Exception as e:
            self.logger.error(f"Unexpected error adding message: {e}")
            return False, "An unexpected error occurred. Please try again."
    
    async def update_session_name(
        self, 
        session_id: str, 
        new_name: str, 
        user_id: str = None
    ) -> bool:
        """
        Update the name of a chat session.
        
        Args:
            session_id: ID of the chat session
            new_name: New name for the session
            user_id: Optional user ID for security check
            
        Returns:
            True if session name was updated successfully, False otherwise
        """
        try:
            if not session_id or not new_name:
                return False
            
            # Get database manager
            db_manager = await get_database_manager()
            
            # Verify session belongs to user if user_id provided
            if user_id:
                session_info = await db_manager.get_session_info(session_id, user_id)
                if not session_info:
                    return False
            
            # Update session name
            await db_manager.execute_query(
                """UPDATE chat_sessions 
                   SET session_name = $1, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = $2""",
                (new_name.strip(), session_id)
            )
            
            self.logger.info(f"Session name updated: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating session name: {e}")
            return False
    
    async def delete_chat_session(self, session_id: str, user_id: str = None) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            session_id: ID of the chat session to delete
            user_id: Optional user ID for security check
            
        Returns:
            True if session was deleted successfully, False otherwise
        """
        try:
            if not session_id:
                return False
            
            # Get database manager
            db_manager = await get_database_manager()
            
            # Verify session belongs to user if user_id provided
            if user_id:
                session_info = await db_manager.get_session_info(session_id, user_id)
                if not session_info:
                    return False
            
            # Mark session as inactive instead of deleting (soft delete)
            await db_manager.execute_query(
                "UPDATE chat_sessions SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                (session_id,)
            )
            
            self.logger.info(f"Chat session deleted (soft): {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting chat session: {e}")
            return False
    
    async def get_session_info(self, session_id: str, user_id: str = None) -> Optional[Dict]:
        """
        Get information about a specific chat session.
        
        Args:
            session_id: ID of the chat session
            user_id: Optional user ID for security check
            
        Returns:
            Dictionary with session information or None if not found/unauthorized
        """
        try:
            if not session_id:
                return None
            
            # Get database manager
            db_manager = await get_database_manager()
            
            session_info = await db_manager.get_session_info(session_id, user_id)
            
            if session_info:
                # Convert UUIDs to strings for JSON serialization
                session_dict = dict(session_info)
                session_dict['id'] = str(session_dict['id'])
                session_dict['user_id'] = str(session_dict['user_id'])
                return session_dict
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting session info: {e}")
            return None
    
    async def get_user_message_count(self, user_id: str) -> int:
        """
        Get total number of messages for a user across all sessions.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Total message count
        """
        try:
            if not user_id:
                return 0
            
            # Get database manager
            db_manager = await get_database_manager()
            
            result = await db_manager.execute_query(
                """SELECT COUNT(cm.id) as total_messages
                   FROM chat_messages cm
                   JOIN chat_sessions cs ON cm.session_id = cs.id
                   WHERE cs.user_id = $1 AND cs.is_active = true""",
                (user_id,),
                fetch_one=True
            )
            
            return result['total_messages'] if result else 0
            
        except Exception as e:
            self.logger.error(f"Error getting user message count: {e}")
            return 0
    
    async def search_messages(
        self, 
        user_id: str, 
        query: str, 
        session_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search messages across user's chat sessions.
        
        Args:
            user_id: ID of the user
            query: Search query
            session_id: Optional specific session to search
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        try:
            if not user_id or not query:
                return []
            
            # Get database manager
            db_manager = await get_database_manager()
            
            if session_id:
                # Search in specific session
                result = await db_manager.execute_query(
                    """SELECT cm.*, cs.session_name
                       FROM chat_messages cm
                       JOIN chat_sessions cs ON cm.session_id = cs.id
                       WHERE cs.user_id = $1 AND cs.id = $2 AND cs.is_active = true
                       AND (cm.content ILIKE $3 OR cm.content ILIKE $4)
                       ORDER BY cm.created_at DESC
                       LIMIT $5""",
                    (user_id, session_id, f"%{query}%", f"%{query.lower()}%", limit),
                    fetch=True
                )
            else:
                # Search across all user sessions
                result = await db_manager.execute_query(
                    """SELECT cm.*, cs.session_name
                       FROM chat_messages cm
                       JOIN chat_sessions cs ON cm.session_id = cs.id
                       WHERE cs.user_id = $1 AND cs.is_active = true
                       AND (cm.content ILIKE $2 OR cm.content ILIKE $3)
                       ORDER BY cm.created_at DESC
                       LIMIT $4""",
                    (user_id, f"%{query}%", f"%{query.lower()}%", limit),
                    fetch=True
                )
            
            # Convert UUIDs to strings for JSON serialization
            messages = []
            for message in result:
                message_dict = dict(message)
                message_dict['id'] = str(message_dict['id'])
                message_dict['session_id'] = str(message_dict['session_id'])
                messages.append(message_dict)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Error searching messages: {e}")
            return []
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old inactive chat sessions.
        
        Args:
            days_old: Number of days old sessions should be to be cleaned up
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Get database manager
            db_manager = await get_database_manager()
            
            deleted_count = await db_manager.cleanup_old_sessions(days_old)
            self.logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0