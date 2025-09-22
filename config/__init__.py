"""
Configuration package for OceanScope.
Contains database and application configuration files.
"""

from .database_config import (
    DatabaseConfig,
    DEFAULT_DB_CONFIG,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    get_database_config
)

__all__ = [
    'DatabaseConfig',
    'DEFAULT_DB_CONFIG',
    'DEVELOPMENT_CONFIG', 
    'PRODUCTION_CONFIG',
    'get_database_config'
]
