"""
Database Manager for handling SQLite database operations.
"""
import sqlite3
import os
import logging
from typing import Any, Optional, List, Dict
from contextlib import contextmanager


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "app_data.db"):
        """Initialize database manager with database path."""
        self.db_path = db_path
        self.is_available = True
        self._setup_logging()
        self.initialize_database()
    
    def _setup_logging(self):
        """Set up logging for database operations."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """)
                
                # Create chat_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_name VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create chat_messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        message_type VARCHAR(10) NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            self.is_available = False
            raise DatabaseError(f"Failed to initialize database: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during database initialization: {e}")
            self.is_available = False
            raise DatabaseError(f"Unexpected database error: {e}")
    
    def check_availability(self) -> bool:
        """Check if database is available and functional."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                self.is_available = True
                return True
        except Exception as e:
            self.logger.error(f"Database availability check failed: {e}")
            self.is_available = False
            return False
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.OperationalError as e:
            self.logger.error(f"Database connection failed: {e}")
            self.is_available = False
            raise DatabaseError(f"Cannot connect to database: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected database connection error: {e}")
            self.is_available = False
            raise DatabaseError(f"Database connection error: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> Any:
        """Execute a query and return results with comprehensive error handling."""
        if not self.is_available:
            raise DatabaseError("Database is not available")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    result = cursor.lastrowid if query.strip().upper().startswith('INSERT') else cursor.rowcount
                    self.logger.debug(f"Query executed successfully: {query[:50]}...")
                    return result
                else:
                    result = cursor.fetchall()
                    self.logger.debug(f"Query executed successfully, returned {len(result)} rows")
                    return result
                    
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Database integrity error: {e}")
            if "UNIQUE constraint failed" in str(e):
                raise DatabaseError("A record with this information already exists")
            elif "FOREIGN KEY constraint failed" in str(e):
                raise DatabaseError("Referenced record does not exist")
            else:
                raise DatabaseError(f"Data integrity error: {e}")
                
        except sqlite3.OperationalError as e:
            self.logger.error(f"Database operational error: {e}")
            self.is_available = False
            if "database is locked" in str(e):
                raise DatabaseError("Database is temporarily unavailable, please try again")
            elif "no such table" in str(e):
                raise DatabaseError("Database structure is corrupted, please contact support")
            else:
                raise DatabaseError(f"Database operation failed: {e}")
                
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error: {e}")
            raise DatabaseError(f"Database error: {e}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error in execute_query: {e}")
            raise DatabaseError(f"Unexpected database error: {e}")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets."""
        if not self.is_available:
            raise DatabaseError("Database is not available")
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                self.logger.debug(f"Batch query executed successfully: {len(params_list)} operations")
                return cursor.rowcount
                
        except sqlite3.Error as e:
            self.logger.error(f"Batch query execution failed: {e}")
            raise DatabaseError(f"Batch operation failed: {e}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error in execute_many: {e}")
            raise DatabaseError(f"Unexpected batch operation error: {e}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username with error handling."""
        try:
            if not username or not isinstance(username, str):
                return None
                
            result = self.execute_query(
                "SELECT * FROM users WHERE username = ?", (username.strip(),)
            )
            return dict(result[0]) if result else None
            
        except DatabaseError:
            raise  # Re-raise database errors
        except Exception as e:
            self.logger.error(f"Error getting user by username: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email with error handling."""
        try:
            if not email or not isinstance(email, str):
                return None
                
            result = self.execute_query(
                "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
            )
            return dict(result[0]) if result else None
            
        except DatabaseError:
            raise  # Re-raise database errors
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID with error handling."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                return None
                
            result = self.execute_query(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            return dict(result[0]) if result else None
            
        except DatabaseError:
            raise  # Re-raise database errors
        except Exception as e:
            self.logger.error(f"Error getting user by ID: {e}")
            raise DatabaseError(f"Failed to retrieve user: {e}")