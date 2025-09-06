import google.generativeai as genai
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import json
from .config import config

class OceanDataQueryEngine:
    """
    Query engine for processing natural language queries about ocean data using Gemini LLM.
    Provides both text responses and data insights for Argo float data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the query engine with Gemini API.
        
        Args:
            api_key: Google Gemini API key. If None, will use configuration.
        """
        self.api_key = api_key or config.gemini_api_key
        self.model_name = config.gemini_model
        self.temperature = config.gemini_temperature
        self.max_tokens = config.gemini_max_tokens
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            st.warning("⚠️ Gemini API key not found. Text responses will be limited.")
    
    # Remove the old _get_api_key method as it's now handled by config
    
    def _convert_to_native_types(self, data: Any) -> Any:
        """
        Convert numpy/pandas data types to native Python types for JSON serialization.
        
        Args:
            data: Input data that may contain numpy types
            
        Returns:
            Data with native Python types
        """
        if isinstance(data, (np.integer, np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.floating, np.float64, np.float32)):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {k: self._convert_to_native_types(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_native_types(item) for item in data]
        else:
            return data
    
    def analyze_data_context(self, df: pd.DataFrame, profile_id: int) -> Dict[str, Any]:
        """
        Analyze the data to provide context for LLM responses.
        
        Args:
            df: DataFrame containing the ocean data
            profile_id: Selected profile ID
            
        Returns:
            Dictionary containing data statistics and insights
        """
        df_prof = df[df["N_PROF"] == profile_id]
        
        if df_prof.empty:
            return {"error": "No data found for the selected profile"}
        
        try:
            # Basic statistics with safe type conversion
            stats = {
                "profile_id": int(profile_id),
                "total_measurements": int(len(df_prof)),
                "depth_range": {
                    "min": float(df_prof["PRES"].min()),
                    "max": float(df_prof["PRES"].max())
                },
                "temperature": {
                    "min": float(df_prof["TEMP"].min()),
                    "max": float(df_prof["TEMP"].max()),
                    "mean": float(df_prof["TEMP"].mean()),
                    "surface": float(df_prof[df_prof["PRES"] == df_prof["PRES"].min()]["TEMP"].iloc[0])
                },
                "salinity": {
                    "min": float(df_prof["PSAL"].min()),
                    "max": float(df_prof["PSAL"].max()),
                    "mean": float(df_prof["PSAL"].mean()),
                    "surface": float(df_prof[df_prof["PRES"] == df_prof["PRES"].min()]["PSAL"].iloc[0])
                }
            }
            
            # Ensure all values are native Python types
            return self._convert_to_native_types(stats)
            
        except Exception as e:
            return {"error": f"Error analyzing data: {str(e)}"}
    
    def create_data_summary(self, stats: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of the data statistics.
        """
        if "error" in stats:
            return stats["error"]
        
        # Safety checks for required keys with defaults
        try:
            profile_id = stats.get('profile_id', 0)
            measurements = stats.get('total_measurements', 0)
            depth_range = stats.get('depth_range', {})
            temp_data = stats.get('temperature', {})
            sal_data = stats.get('salinity', {})
            
            summary = f"""
            **Argo Float Profile {profile_id} Summary:**
            
            📊 **Measurements**: {measurements} data points
            🌊 **Depth Range**: {depth_range.get('min', 0):.1f} - {depth_range.get('max', 0):.1f} dbar
            
            🌡️ **Temperature Profile**:
            - Surface: {temp_data.get('surface', 0):.2f}°C
            - Range: {temp_data.get('min', 0):.2f}°C to {temp_data.get('max', 0):.2f}°C
            - Average: {temp_data.get('mean', 0):.2f}°C
            
            🧂 **Salinity Profile**:
            - Surface: {sal_data.get('surface', 0):.2f} PSU
            - Range: {sal_data.get('min', 0):.2f} to {sal_data.get('max', 0):.2f} PSU
            - Average: {sal_data.get('mean', 0):.2f} PSU
            """
            return summary
        except Exception as e:
            return f"Error creating data summary: {str(e)}"
    
    def generate_response(self, query: str, data_stats: Dict[str, Any]) -> str:
        """
        Generate a response using Gemini LLM based on the query and data context.
        
        Args:
            query: User's natural language query
            data_stats: Data statistics and context
            
        Returns:
            LLM-generated response text
        """
        if not self.model:
            return self._fallback_response(query, data_stats)
        
        # Create context-rich prompt
        try:
            # Convert data_stats to JSON with proper serialization
            data_context = json.dumps(data_stats, indent=2, default=str)
        except (TypeError, ValueError) as json_error:
            st.warning(f"Data serialization issue: {json_error}. Using simplified context.")
            # Create a simplified context if JSON serialization fails
            data_context = f"Profile {data_stats.get('profile_id', 'Unknown')}: {data_stats.get('total_measurements', 0)} measurements"
        
        prompt = f"""
        You are an expert oceanographer analyzing Argo float data. A user has asked a question about ocean data.
        
        **User Query**: {query}
        
        **Available Data Context**:
        {data_context}
        
        Please provide a comprehensive, scientific response that:
        1. Directly answers the user's question
        2. Uses the specific data values provided
        3. Explains oceanographic concepts if relevant
        4. Provides scientific insights about the measurements
        5. Keeps the language accessible but scientifically accurate
        
        If the query is about temperature, salinity, pressure, or ocean profiles, use the actual data values.
        If asking about trends or patterns, analyze the provided statistics.
        
        Format your response in a clear, informative way suitable for both scientists and students.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error generating LLM response: {str(e)}")
            return self._fallback_response(query, data_stats)
    
    def _fallback_response(self, query: str, data_stats: Dict[str, Any]) -> str:
        """
        Provide a fallback response when LLM is not available.
        """
        summary = self.create_data_summary(data_stats)
        
        fallback = f"""
        **Analysis Based on Available Data:**
        
        {summary}
        
        📝 **Response to your query**: "{query}"
        
        I can see you're interested in the oceanographic data. The profile shows typical ocean characteristics 
        with temperature and salinity variations with depth. For more detailed AI-powered analysis, 
        please configure the Gemini API key.
        
        **Key Observations**:
        - The data represents a complete ocean profile from surface to depth
        - Temperature typically decreases with increasing pressure (depth)
        - Salinity patterns can indicate water mass characteristics
        """
        
        return fallback
    
    def process_query(self, query: str, df: pd.DataFrame, profile_id: int) -> Tuple[str, Dict[str, Any]]:
        """
        Process a complete user query and return both text response and data context.
        
        Args:
            query: User's natural language query
            df: DataFrame containing ocean data
            profile_id: Selected profile ID
            
        Returns:
            Tuple of (response_text, data_statistics)
        """
        # Analyze the data context
        data_stats = self.analyze_data_context(df, profile_id)
        
        # Generate LLM response
        response_text = self.generate_response(query, data_stats)
        
        return response_text, data_stats