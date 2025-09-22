"""
Database configuration for OceanScope PostgreSQL setup.
"""
import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration class."""
    
    # Database connection parameters
    host: str = "localhost"
    port: int = 5432
    database: str = "oceanscope"
    username: str = "postgres"
    password: str = ""
    
    # Connection pool settings
    min_connections: int = 1
    max_connections: int = 10
    
    # Connection timeout settings
    connect_timeout: int = 30
    command_timeout: int = 60
    
    # SSL settings
    ssl_mode: str = "prefer"
    
    def __post_init__(self):
        """Load configuration from environment variables if available."""
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", self.port))
        self.database = os.getenv("DB_NAME", self.database)
        self.username = os.getenv("DB_USER", self.username)
        self.password = os.getenv("DB_PASSWORD", self.password)
        
        # Pool settings from environment
        self.min_connections = int(os.getenv("DB_MIN_CONNECTIONS", self.min_connections))
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", self.max_connections))
        
        # Timeout settings from environment
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", self.connect_timeout))
        self.command_timeout = int(os.getenv("DB_COMMAND_TIMEOUT", self.command_timeout))
        
        # SSL settings from environment
        self.ssl_mode = os.getenv("DB_SSL_MODE", self.ssl_mode)
    
    @property
    def connection_string(self) -> str:
        """Get the PostgreSQL connection string."""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.ssl_mode}"
        )
    
    @property
    def dsn(self) -> str:
        """Get the PostgreSQL DSN (Data Source Name)."""
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.username} "
            f"password={self.password} "
            f"sslmode={self.ssl_mode}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "connect_timeout": self.connect_timeout,
            "command_timeout": self.command_timeout,
            "ssl_mode": self.ssl_mode
        }
    
    def validate(self) -> bool:
        """Validate the database configuration."""
        if not all([self.host, self.database, self.username]):
            return False
        
        if self.port <= 0 or self.port > 65535:
            return False
        
        if self.min_connections < 0 or self.max_connections < self.min_connections:
            return False
        
        return True


# Default database configuration
DEFAULT_DB_CONFIG = DatabaseConfig()

# Environment-specific configurations
DEVELOPMENT_CONFIG = DatabaseConfig(
    host="localhost",
    port=5432,
    database="oceanscope",
    username="postgres",
    password="",  # Will be loaded from environment
    ssl_mode="disable"
)

PRODUCTION_CONFIG = DatabaseConfig(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "oceanscope"),
    username=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
    ssl_mode=os.getenv("DB_SSL_MODE", "require"),
    min_connections=5,
    max_connections=20
)

# Get configuration based on environment
def get_database_config() -> DatabaseConfig:
    """Get database configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return PRODUCTION_CONFIG
    elif env == "development":
        return DEVELOPMENT_CONFIG
    else:
        return DEFAULT_DB_CONFIG
