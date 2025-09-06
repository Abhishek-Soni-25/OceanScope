"""
Configuration management for OceanScope application.
Centralizes environment variable handling and provides type-safe configuration access.
"""

import os
from typing import Optional, Union
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Centralized configuration management for OceanScope.
    Handles environment variables with proper defaults and type conversion.
    """
    
    # API Configuration
    @property
    def gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from environment variables or Streamlit secrets."""
        # Priority: .env file -> system environment -> streamlit secrets
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            return api_key
        
        # Fallback to streamlit secrets
        try:
            return st.secrets.get("GEMINI_API_KEY")
        except (KeyError, FileNotFoundError, AttributeError):
            return None
    
    @property
    def gemini_model(self) -> str:
        """Get Gemini model name."""
        return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    @property
    def gemini_temperature(self) -> float:
        """Get Gemini response temperature (creativity)."""
        return float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    
    @property
    def gemini_max_tokens(self) -> int:
        """Get maximum tokens for Gemini responses."""
        return int(os.getenv("GEMINI_MAX_TOKENS", "1000"))
    
    # Data Configuration
    @property
    def data_file_path(self) -> str:
        """Get path to the NetCDF data file."""
        return os.getenv("DATA_FILE_PATH", "data/20250101_prof.nc")
    
    @property
    def max_profiles_display(self) -> int:
        """Get maximum number of profiles to display in UI."""
        return int(os.getenv("MAX_PROFILES_DISPLAY", "100"))
    
    # Application Configuration
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    # UI Configuration
    @property
    def show_advanced_stats(self) -> bool:
        """Check if advanced statistics should be shown by default."""
        return os.getenv("SHOW_ADVANCED_STATS", "true").lower() == "true"
    
    @property
    def default_profile_id(self) -> int:
        """Get default profile ID for initial selection."""
        return int(os.getenv("DEFAULT_PROFILE_ID", "0"))
    
    @property
    def enable_experimental_features(self) -> bool:
        """Check if experimental features are enabled."""
        return os.getenv("ENABLE_EXPERIMENTAL_FEATURES", "false").lower() == "true"
    
    def get_env_info(self) -> dict:
        """
        Get information about current environment configuration.
        Useful for debugging and setup verification.
        """
        return {
            "gemini_api_configured": bool(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "data_file_path": self.data_file_path,
            "debug_mode": self.debug,
            "cache_enabled": self.cache_enabled,
            "log_level": self.log_level
        }
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate current configuration and return status with any issues.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check API key
        if not self.gemini_api_key:
            issues.append("Gemini API key not configured - AI responses will be limited")
        
        # Check data file
        if not os.path.exists(self.data_file_path):
            issues.append(f"Data file not found: {self.data_file_path}")
        
        # Check temperature range
        if not (0.0 <= self.gemini_temperature <= 2.0):
            issues.append(f"Gemini temperature out of range: {self.gemini_temperature}")
        
        # Check max tokens
        if self.gemini_max_tokens <= 0:
            issues.append(f"Invalid max tokens value: {self.gemini_max_tokens}")
        
        is_valid = len(issues) == 0
        return is_valid, issues

# Global configuration instance
config = Config()