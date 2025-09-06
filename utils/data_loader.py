import xarray as xr
import pandas as pd
import streamlit as st
from typing import Tuple, Dict, Any, List
import numpy as np
from .config import config

class ArgoDataLoader:
    """
    Enhanced data loader for Argo float NetCDF files with analysis capabilities.
    """
    
    def __init__(self, file_path: str = None):
        """
        Initialize the data loader.
        
        Args:
            file_path: Path to the NetCDF file. If None, will use configuration.
        """
        self.file_path = file_path or config.data_file_path
        self.max_profiles_display = config.max_profiles_display
        self.cache_enabled = config.cache_enabled
        self._dataset = None
        self._dataframe = None
    
    @st.cache_data
    def load_dataset(_self) -> xr.Dataset:
        """
        Load the NetCDF dataset with caching.
        
        Returns:
            xarray Dataset containing the Argo data
        """
        try:
            _self._dataset = xr.open_dataset(_self.file_path)
            return _self._dataset
        except Exception as e:
            st.error(f"Error loading dataset: {str(e)}")
            return None
    
    @st.cache_data
    def get_dataframe(_self) -> pd.DataFrame:
        """
        Convert dataset to pandas DataFrame with caching.
        
        Returns:
            pandas DataFrame with PRES, TEMP, PSAL columns
        """
        if _self._dataset is None:
            _self._dataset = _self.load_dataset()
        
        if _self._dataset is not None:
            # Select key oceanographic variables
            df = _self._dataset[["PRES", "TEMP", "PSAL"]].to_dataframe().reset_index()
            
            # Clean the data - remove NaN values
            df = df.dropna()
            
            # Sort by profile and pressure for consistent ordering
            df = df.sort_values(["N_PROF", "PRES"])
            
            _self._dataframe = df
            return df
        
        return pd.DataFrame()
    
    def get_profile_data(self, profile_id: int) -> pd.DataFrame:
        """
        Get data for a specific profile.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            DataFrame containing data for the specified profile
        """
        df = self.get_dataframe()
        return df[df["N_PROF"] == profile_id].copy()
    
    def get_available_profiles(self) -> List[int]:
        """
        Get list of available profile IDs.
        
        Returns:
            List of profile IDs
        """
        df = self.get_dataframe()
        return sorted(df["N_PROF"].unique())
    
    def get_profile_summary(self, profile_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics for a profile.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Dictionary containing profile statistics
        """
        df_prof = self.get_profile_data(profile_id)
        
        if df_prof.empty:
            return {"error": f"Profile {profile_id} not found"}
        
        # Calculate oceanographic insights
        temp_gradient = self._calculate_gradient(df_prof, "TEMP", "PRES")
        sal_gradient = self._calculate_gradient(df_prof, "PSAL", "PRES")
        
        summary = {
            "profile_id": profile_id,
            "measurements": len(df_prof),
            "depth_info": {
                "min_pressure": float(df_prof["PRES"].min()),
                "max_pressure": float(df_prof["PRES"].max()),
                "depth_span": float(df_prof["PRES"].max() - df_prof["PRES"].min())
            },
            "temperature": {
                "surface": float(df_prof.iloc[0]["TEMP"]),
                "bottom": float(df_prof.iloc[-1]["TEMP"]),
                "min": float(df_prof["TEMP"].min()),
                "max": float(df_prof["TEMP"].max()),
                "mean": float(df_prof["TEMP"].mean()),
                "std": float(df_prof["TEMP"].std()),
                "gradient": temp_gradient
            },
            "salinity": {
                "surface": float(df_prof.iloc[0]["PSAL"]),
                "bottom": float(df_prof.iloc[-1]["PSAL"]),
                "min": float(df_prof["PSAL"].min()),
                "max": float(df_prof["PSAL"].max()),
                "mean": float(df_prof["PSAL"].mean()),
                "std": float(df_prof["PSAL"].std()),
                "gradient": sal_gradient
            },
            "ocean_characteristics": self._analyze_water_mass_characteristics(df_prof)
        }
        
        return summary
    
    def _calculate_gradient(self, df: pd.DataFrame, variable: str, depth_var: str = "PRES") -> float:
        """
        Calculate the average gradient of a variable with depth.
        
        Args:
            df: DataFrame containing the data
            variable: Variable name (TEMP or PSAL)
            depth_var: Depth variable name (PRES)
            
        Returns:
            Average gradient value
        """
        if len(df) < 2:
            return 0.0
        
        # Calculate gradient using numpy gradient function
        gradient = np.gradient(df[variable].values, df[depth_var].values)
        return float(np.mean(gradient))
    
    def _analyze_water_mass_characteristics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze water mass characteristics based on temperature and salinity.
        
        Args:
            df: DataFrame containing profile data
            
        Returns:
            Dictionary with water mass analysis
        """
        characteristics = {}
        
        # Surface layer analysis (top 10% of measurements)
        surface_idx = max(1, len(df) // 10)
        surface_data = df.iloc[:surface_idx]
        
        # Deep layer analysis (bottom 10% of measurements)
        deep_data = df.iloc[-surface_idx:]
        
        characteristics["surface_layer"] = {
            "avg_temp": float(surface_data["TEMP"].mean()),
            "avg_salinity": float(surface_data["PSAL"].mean()),
            "depth_range": f"{float(surface_data['PRES'].min()):.1f}-{float(surface_data['PRES'].max()):.1f} dbar"
        }
        
        characteristics["deep_layer"] = {
            "avg_temp": float(deep_data["TEMP"].mean()),
            "avg_salinity": float(deep_data["PSAL"].mean()),
            "depth_range": f"{float(deep_data['PRES'].min()):.1f}-{float(deep_data['PRES'].max()):.1f} dbar"
        }
        
        # Temperature stratification
        temp_diff = surface_data["TEMP"].mean() - deep_data["TEMP"].mean()
        characteristics["stratification"] = {
            "temperature_difference": float(temp_diff),
            "is_stratified": temp_diff > 1.0,  # Arbitrary threshold
            "stratification_strength": "strong" if temp_diff > 10 else "moderate" if temp_diff > 5 else "weak"
        }
        
        return characteristics
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the entire dataset.
        
        Returns:
            Dictionary containing dataset information
        """
        dataset = self.load_dataset()
        df = self.get_dataframe()
        
        if dataset is None or df.empty:
            return {"error": "Could not load dataset"}
        
        info = {
            "total_profiles": len(self.get_available_profiles()),
            "total_measurements": len(df),
            "variables": list(dataset.data_vars.keys()),
            "dimensions": dict(dataset.dims),
            "global_attributes": dict(dataset.attrs) if hasattr(dataset, 'attrs') else {},
            "data_range": {
                "pressure": {
                    "min": float(df["PRES"].min()),
                    "max": float(df["PRES"].max())
                },
                "temperature": {
                    "min": float(df["TEMP"].min()),
                    "max": float(df["TEMP"].max())
                },
                "salinity": {
                    "min": float(df["PSAL"].min()),
                    "max": float(df["PSAL"].max())
                }
            }
        }
        
        return info