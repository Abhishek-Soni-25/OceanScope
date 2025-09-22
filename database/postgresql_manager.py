"""
PostgreSQL Database Manager for OceanScope.
Handles all database operations using asyncpg for PostgreSQL.
"""
import asyncio
import logging
import uuid
from typing import Any, Optional, List, Dict, Union
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    CheckViolationError,
    InvalidTextRepresentationError,
    ConnectionDoesNotExistError,
    InterfaceError
)

from config.database_config import get_database_config, DatabaseConfig


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Exception raised when database query fails."""
    pass


class PostgreSQLManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize PostgreSQL manager with configuration."""
        self.config = config or get_database_config()
        self.pool: Optional[Pool] = None
        self.is_available = True
        self._setup_logging()
        
        if not self.config.validate():
            raise DatabaseError("Invalid database configuration")
    
    def _setup_logging(self):
        """Set up logging for database operations."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    'application_name': 'oceanscope',
                    'timezone': 'UTC'
                }
            )
            self.is_available = True
            self.logger.info("PostgreSQL connection pool initialized successfully")
            
            # Test connection
            await self.check_availability()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            self.is_available = False
            raise ConnectionError(f"Failed to initialize database: {e}")
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.logger.info("PostgreSQL connection pool closed")
    
    async def check_availability(self) -> bool:
        """Check if database is available and functional."""
        try:
            if not self.pool:
                return False
                
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                self.is_available = True
                return True
                
        except Exception as e:
            self.logger.error(f"Database availability check failed: {e}")
            self.is_available = False
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool with context manager."""
        if not self.pool:
            raise ConnectionError("Database pool not initialized")
        
        conn = None
        try:
            conn = await self.pool.acquire()
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def execute_query(
        self, 
        query: str, 
        params: tuple = (), 
        fetch: bool = False,
        fetch_one: bool = False
    ) -> Any:
        """Execute a query and return results with comprehensive error handling."""
        if not self.is_available:
            raise DatabaseError("Database is not available")
        
        try:
            async with self.get_connection() as conn:
                if fetch_one:
                    result = await conn.fetchrow(query, *params)
                    return dict(result) if result else None
                elif fetch:
                    result = await conn.fetch(query, *params)
                    return [dict(row) for row in result]
                else:
                    result = await conn.execute(query, *params)
                    return result
                    
        except UniqueViolationError as e:
            self.logger.warning(f"Unique constraint violation: {e}")
            raise QueryError("A record with this information already exists")
            
        except ForeignKeyViolationError as e:
            self.logger.warning(f"Foreign key constraint violation: {e}")
            raise QueryError("Referenced record does not exist")
            
        except CheckViolationError as e:
            self.logger.warning(f"Check constraint violation: {e}")
            raise QueryError("Data validation failed")
            
        except InvalidTextRepresentationError as e:
            self.logger.warning(f"Invalid data format: {e}")
            raise QueryError("Invalid data format provided")
            
        except ConnectionDoesNotExistError as e:
            self.logger.error(f"Database connection lost: {e}")
            self.is_available = False
            raise ConnectionError("Database connection lost")
            
        except InterfaceError as e:
            self.logger.error(f"Database interface error: {e}")
            self.is_available = False
            raise ConnectionError("Database interface error")
            
        except Exception as e:
            self.logger.error(f"Unexpected database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets."""
        if not self.is_available:
            raise DatabaseError("Database is not available")
        
        try:
            async with self.get_connection() as conn:
                result = await conn.executemany(query, params_list)
                self.logger.debug(f"Batch query executed: {len(params_list)} operations")
                return result
                
        except Exception as e:
            self.logger.error(f"Batch query execution failed: {e}")
            raise DatabaseError(f"Batch operation failed: {e}")
    
    async def execute_transaction(self, queries: List[tuple]) -> List[Any]:
        """Execute multiple queries in a transaction."""
        if not self.is_available:
            raise DatabaseError("Database is not available")
        
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    results = []
                    for query, params in queries:
                        if query.strip().upper().startswith(('SELECT', 'WITH')):
                            result = await conn.fetch(query, *params)
                            results.append([dict(row) for row in result])
                        else:
                            result = await conn.execute(query, *params)
                            results.append(result)
                    
                    self.logger.debug(f"Transaction executed: {len(queries)} queries")
                    return results
                    
        except Exception as e:
            self.logger.error(f"Transaction execution failed: {e}")
            raise DatabaseError(f"Transaction failed: {e}")
    
    # User-related methods
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            if not username or not isinstance(username, str):
                return None
                
            result = await self.execute_query(
                "SELECT * FROM users WHERE username = $1 AND is_active = true",
                (username.strip(),),
                fetch_one=True
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting user by username: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        try:
            if not email or not isinstance(email, str):
                return None
                
            result = await self.execute_query(
                "SELECT * FROM users WHERE email = $1 AND is_active = true",
                (email.strip().lower(),),
                fetch_one=True
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")
    
    async def get_user_by_id(self, user_id: Union[str, uuid.UUID]) -> Optional[Dict]:
        """Get user by ID."""
        try:
            if not user_id:
                return None
                
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            result = await self.execute_query(
                "SELECT * FROM users WHERE id = $1 AND is_active = true",
                (user_id,),
                fetch_one=True
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")
    
    async def create_user(
        self, 
        username: str, 
        email: str, 
        password_hash: str,
        first_name: str = None,
        last_name: str = None
    ) -> uuid.UUID:
        """Create a new user."""
        try:
            user_id = await self.execute_query(
                """INSERT INTO users (username, email, password_hash, first_name, last_name)
                   VALUES ($1, $2, $3, $4, $5)
                   RETURNING id""",
                (username.strip(), email.strip().lower(), password_hash, first_name, last_name),
                fetch_one=True
            )
            
            if user_id:
                # Create user profile
                await self.execute_query(
                    "INSERT INTO user_profiles (user_id) VALUES ($1)",
                    (user_id['id'],)
                )
                
                # Create user preferences
                await self.execute_query(
                    "INSERT INTO user_preferences (user_id) VALUES ($1)",
                    (user_id['id'],)
                )
                
                self.logger.info(f"User created successfully: {username}")
                return user_id['id']
            else:
                raise DatabaseError("Failed to create user")
                
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise DatabaseError(f"Failed to create user: {e}")
    
    async def update_user_last_login(self, user_id: Union[str, uuid.UUID]) -> None:
        """Update user's last login timestamp."""
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            await self.execute_query(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
                (user_id,)
            )
            
        except Exception as e:
            self.logger.error(f"Error updating last login: {e}")
            # Don't raise error for this non-critical operation
    
    # Chat-related methods
    async def create_chat_session(
        self, 
        user_id: Union[str, uuid.UUID], 
        session_name: str,
        description: str = None
    ) -> uuid.UUID:
        """Create a new chat session."""
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            result = await self.execute_query(
                """INSERT INTO chat_sessions (user_id, session_name, description)
                   VALUES ($1, $2, $3)
                   RETURNING id""",
                (user_id, session_name.strip(), description),
                fetch_one=True
            )
            
            if result:
                self.logger.info(f"Chat session created: {result['id']}")
                return result['id']
            else:
                raise DatabaseError("Failed to create chat session")
                
        except Exception as e:
            self.logger.error(f"Error creating chat session: {e}")
            raise DatabaseError(f"Failed to create chat session: {e}")
    
    async def get_user_chat_sessions(self, user_id: Union[str, uuid.UUID]) -> List[Dict]:
        """Get all chat sessions for a user."""
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            result = await self.execute_query(
                """SELECT cs.*, 
                          COALESCE(cs.message_count, 0) as message_count,
                          cs.last_message_at
                   FROM chat_sessions cs
                   WHERE cs.user_id = $1 AND cs.is_active = true
                   ORDER BY cs.updated_at DESC""",
                (user_id,),
                fetch=True
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting chat sessions: {e}")
            raise DatabaseError(f"Failed to retrieve chat sessions: {e}")
    
    async def get_chat_messages(
        self, 
        session_id: Union[str, uuid.UUID], 
        user_id: Union[str, uuid.UUID] = None
    ) -> List[Dict]:
        """Get all messages for a chat session."""
        try:
            if isinstance(session_id, str):
                session_id = uuid.UUID(session_id)
            if user_id and isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            if user_id:
                # Verify session belongs to user
                session_check = await self.execute_query(
                    "SELECT user_id FROM chat_sessions WHERE id = $1",
                    (session_id,),
                    fetch_one=True
                )
                
                if not session_check or session_check['user_id'] != user_id:
                    raise DatabaseError("Unauthorized access to chat session")
            
            result = await self.execute_query(
                """SELECT * FROM chat_messages 
                   WHERE session_id = $1 
                   ORDER BY created_at ASC""",
                (session_id,),
                fetch=True
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting chat messages: {e}")
            raise DatabaseError(f"Failed to retrieve chat messages: {e}")
    
    async def add_chat_message(
        self, 
        session_id: Union[str, uuid.UUID], 
        message_type: str, 
        content: str,
        user_id: Union[str, uuid.UUID] = None,
        metadata: Dict = None
    ) -> uuid.UUID:
        """Add a message to a chat session."""
        try:
            if isinstance(session_id, str):
                session_id = uuid.UUID(session_id)
            if user_id and isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            if user_id:
                # Verify session belongs to user
                session_check = await self.execute_query(
                    "SELECT user_id FROM chat_sessions WHERE id = $1",
                    (session_id,),
                    fetch_one=True
                )
                
                if not session_check or session_check['user_id'] != user_id:
                    raise DatabaseError("Unauthorized access to chat session")
            
            # Limit message length
            if len(content) > 10000:
                content = content[:10000] + "... [message truncated]"
            
            result = await self.execute_query(
                """INSERT INTO chat_messages (session_id, message_type, content, metadata)
                   VALUES ($1, $2, $3, $4)
                   RETURNING id""",
                (session_id, message_type, content.strip(), metadata),
                fetch_one=True
            )
            
            if result:
                self.logger.debug(f"Message added to session {session_id}")
                return result['id']
            else:
                raise DatabaseError("Failed to add message")
                
        except Exception as e:
            self.logger.error(f"Error adding chat message: {e}")
            raise DatabaseError(f"Failed to add message: {e}")
    
    async def get_session_info(
        self, 
        session_id: Union[str, uuid.UUID], 
        user_id: Union[str, uuid.UUID] = None
    ) -> Optional[Dict]:
        """Get information about a chat session."""
        try:
            if isinstance(session_id, str):
                session_id = uuid.UUID(session_id)
            if user_id and isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
                
            if user_id:
                result = await self.execute_query(
                    """SELECT cs.*, COALESCE(cs.message_count, 0) as message_count
                       FROM chat_sessions cs
                       WHERE cs.id = $1 AND cs.user_id = $2 AND cs.is_active = true""",
                    (session_id, user_id),
                    fetch_one=True
                )
            else:
                result = await self.execute_query(
                    """SELECT cs.*, COALESCE(cs.message_count, 0) as message_count
                       FROM chat_sessions cs
                       WHERE cs.id = $1 AND cs.is_active = true""",
                    (session_id,),
                    fetch_one=True
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting session info: {e}")
            raise DatabaseError(f"Failed to retrieve session info: {e}")
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old inactive chat sessions."""
        try:
            result = await self.execute_query(
                "SELECT cleanup_old_sessions($1)",
                (days_old,),
                fetch_one=True
            )
            
            deleted_count = result['cleanup_old_sessions'] if result else 0
            self.logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0


# Global database manager instance
_db_manager: Optional[PostgreSQLManager] = None


async def get_database_manager() -> PostgreSQLManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = PostgreSQLManager()
        await _db_manager.initialize()
    return _db_manager


async def close_database_manager():
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
