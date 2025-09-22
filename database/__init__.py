"""
Database package for OceanScope.
Contains PostgreSQL database management and schema files.
"""

from .postgresql_manager import (
    PostgreSQLManager,
    DatabaseError,
    ConnectionError,
    QueryError,
    get_database_manager,
    close_database_manager
)

__all__ = [
    'PostgreSQLManager',
    'DatabaseError', 
    'ConnectionError',
    'QueryError',
    'get_database_manager',
    'close_database_manager'
]
