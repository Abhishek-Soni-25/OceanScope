import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
from utils.query_engine import OceanDataQueryEngine
from utils.data_loader import ArgoDataLoader

st.title("🤖 Chat with Argo Data")

# Initialize components
@st.cache_resource
def init_components():
    """Initialize data loader and query engine with caching."""
    data_loader = ArgoDataLoader()
    query_engine = OceanDataQueryEngine()
    return data_loader, query_engine

data_loader, query_engine = init_components()

# Load data
try:
    df = data_loader.get_dataframe()
    available_profiles = data_loader.get_available_profiles()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Sidebar for profile selection
with st.sidebar:
    st.subheader("🔧 Configuration")
    
    # Profile selection
    if available_profiles:
        selected_profile = st.selectbox(
            "Select Profile for Analysis",
            available_profiles,
            index=0,
            help="Choose which ocean profile to analyze"
        )
    else:
        st.error("No profiles available")
        st.stop()
    
    # Display options
    st.subheader("📊 Display Options")
    show_data_summary = st.checkbox("Show Data Summary", value=True)
    show_visualizations = st.checkbox("Show Plots", value=True)
    show_advanced_stats = st.checkbox("Show Advanced Statistics", value=False)

# Main interface
st.subheader("💬 Ask Questions About Ocean Data")

# Input query
query = st.text_input(
    "Enter your question about the oceanographic data:",
    placeholder="e.g., What can you tell me about the temperature profile?",
    help="Ask questions about temperature, salinity, pressure, or ocean characteristics"
)

# Example queries
with st.expander("💡 Example Questions"):
    example_queries = [
        "What can you tell me about the temperature profile?",
        "How does salinity change with depth in this profile?",
        "What are the characteristics of this water mass?",
        "Is this ocean profile stratified?",
        "What's the temperature gradient in this profile?",
        "Compare the surface and deep water properties",
        "What oceanographic insights can you provide?"
    ]
    
    for i, example in enumerate(example_queries):
        if st.button(f"📝 {example}", key=f"example_{i}"):
            query = example
            st.rerun()

if query:
    st.write(f"🔎 **Your Question**: {query}")
    
    # Create tabs for organized display
    tab1, tab2, tab3 = st.tabs(["🤖 AI Response", "📊 Data Analysis", "📈 Visualizations"])
    
    with tab1:
        st.subheader("AI-Powered Analysis")
        
        with st.spinner("🧠 Analyzing data and generating response..."):
            try:
                # Get AI response and data context
                response_text, data_stats = query_engine.process_query(
                    query, df, selected_profile
                )
                
                # Display AI response
                st.markdown(response_text)
                
            except Exception as e:
                st.error(f"Error generating AI response: {str(e)}")
                # Fallback to basic analysis using data loader
                try:
                    profile_summary = data_loader.get_profile_summary(selected_profile)
                    if "error" not in profile_summary:
                        # Create a simple summary from profile data
                        fallback_summary = f"""
                        **Profile {selected_profile} Analysis:**
                        
                        📊 **Measurements**: {profile_summary['measurements']} data points
                        🌊 **Depth Range**: {profile_summary['depth_info']['min_pressure']:.1f} - {profile_summary['depth_info']['max_pressure']:.1f} dbar
                        
                        🌡️ **Temperature**:
                        - Surface: {profile_summary['temperature']['surface']:.2f}°C
                        - Range: {profile_summary['temperature']['min']:.2f}°C to {profile_summary['temperature']['max']:.2f}°C
                        - Average: {profile_summary['temperature']['mean']:.2f}°C
                        
                        🧂 **Salinity**:
                        - Surface: {profile_summary['salinity']['surface']:.2f} PSU
                        - Range: {profile_summary['salinity']['min']:.2f} to {profile_summary['salinity']['max']:.2f} PSU
                        - Average: {profile_summary['salinity']['mean']:.2f} PSU
                        
                        **Response to your query**: "{query}"
                        
                        The data shows typical oceanographic characteristics. For detailed AI analysis, please check your Gemini API configuration.
                        """
                        st.markdown(fallback_summary)
                    else:
                        st.warning(profile_summary["error"])
                except Exception as fallback_error:
                    st.error(f"Unable to analyze data: {str(fallback_error)}")
                    st.info("Please check your data file and try again.")
    
    with tab2:
        st.subheader("Detailed Data Analysis")
        
        # Get comprehensive profile summary
        profile_summary = data_loader.get_profile_summary(selected_profile)
        
        if "error" not in profile_summary:
            # Display summary statistics
            if show_data_summary:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "📏 Measurements",
                        profile_summary["measurements"]
                    )
                    st.metric(
                        "🌡️ Surface Temp",
                        f"{profile_summary['temperature']['surface']:.2f}°C"
                    )
                
                with col2:
                    st.metric(
                        "🌊 Max Depth",
                        f"{profile_summary['depth_info']['max_pressure']:.1f} dbar"
                    )
                    st.metric(
                        "🧂 Surface Salinity",
                        f"{profile_summary['salinity']['surface']:.2f} PSU"
                    )
                
                with col3:
                    st.metric(
                        "📐 Temp Range",
                        f"{profile_summary['temperature']['max'] - profile_summary['temperature']['min']:.2f}°C"
                    )
                    st.metric(
                        "🔄 Sal Range",
                        f"{profile_summary['salinity']['max'] - profile_summary['salinity']['min']:.2f} PSU"
                    )
            
            # Advanced statistics
            if show_advanced_stats:
                st.subheader("🔬 Advanced Analysis")
                
                # Water mass characteristics
                water_chars = profile_summary["ocean_characteristics"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Surface Layer Analysis**")
                    surface = water_chars["surface_layer"]
                    st.write(f"- Temperature: {surface['avg_temp']:.2f}°C")
                    st.write(f"- Salinity: {surface['avg_salinity']:.2f} PSU")
                    st.write(f"- Depth Range: {surface['depth_range']}")
                
                with col2:
                    st.write("**Deep Layer Analysis**")
                    deep = water_chars["deep_layer"]
                    st.write(f"- Temperature: {deep['avg_temp']:.2f}°C")
                    st.write(f"- Salinity: {deep['avg_salinity']:.2f} PSU")
                    st.write(f"- Depth Range: {deep['depth_range']}")
                
                # Stratification info
                strat = water_chars["stratification"]
                st.write("**Stratification Analysis**")
                st.write(f"- Temperature Difference (Surface-Deep): {strat['temperature_difference']:.2f}°C")
                st.write(f"- Stratification Strength: {strat['stratification_strength'].title()}")
                st.write(f"- Is Stratified: {'Yes' if strat['is_stratified'] else 'No'}")
        else:
            st.error(profile_summary["error"])
    
    with tab3:
        if show_visualizations:
            st.subheader("Data Visualizations")
            
            # Get profile data
            df_prof = data_loader.get_profile_data(selected_profile)
            
            if not df_prof.empty:
                # Create enhanced plots
                fig, axes = plt.subplots(1, 3, figsize=(15, 6))
                
                # Temperature profile
                axes[0].plot(df_prof["TEMP"], df_prof["PRES"], 
                           'b-', linewidth=2, label="Temperature")
                axes[0].invert_yaxis()
                axes[0].set_xlabel("Temperature (°C)")
                axes[0].set_ylabel("Pressure (dbar)")
                axes[0].set_title(f"Temperature Profile\n(Profile {selected_profile})")
                axes[0].grid(True, alpha=0.3)
                
                # Salinity profile
                axes[1].plot(df_prof["PSAL"], df_prof["PRES"], 
                           'orange', linewidth=2, label="Salinity")
                axes[1].invert_yaxis()
                axes[1].set_xlabel("Salinity (PSU)")
                axes[1].set_ylabel("Pressure (dbar)")
                axes[1].set_title(f"Salinity Profile\n(Profile {selected_profile})")
                axes[1].grid(True, alpha=0.3)
                
                # T-S diagram
                axes[2].scatter(df_prof["PSAL"], df_prof["TEMP"], 
                              c=df_prof["PRES"], cmap='viridis', s=30)
                axes[2].set_xlabel("Salinity (PSU)")
                axes[2].set_ylabel("Temperature (°C)")
                axes[2].set_title(f"T-S Diagram\n(Color = Pressure)")
                cbar = plt.colorbar(axes[2].collections[0], ax=axes[2])
                cbar.set_label("Pressure (dbar)")
                axes[2].grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Data table
                with st.expander("📋 View Raw Data"):
                    st.dataframe(
                        df_prof[["PRES", "TEMP", "PSAL"]].round(3),
                        use_container_width=True
                    )
            else:
                st.warning(f"No data available for profile {selected_profile}")

# Footer with information
st.markdown("---")
st.markdown("""
**🔧 Technical Notes:**
- AI responses powered by Google Gemini LLM (when API key is configured)
- Data analysis includes gradient calculations and water mass characteristics
- Visualizations show standard oceanographic profiles and T-S diagrams
- All data is cached for performance optimization
""")