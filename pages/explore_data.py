import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
from utils.data_loader import ArgoDataLoader
from utils.auth_decorators import AuthMiddleware

# Configure page
st.set_page_config(
    page_title="Explore Data - OceanScope",
    page_icon="📊",
    layout="wide"
)

# Set up authentication for this protected page
AuthMiddleware.setup_page_auth(require_auth=True, page_name="explore_data.py", show_header=True)

st.title("📊 Explore Argo Data")

# Sidebar navigation
with st.sidebar:
    st.subheader("🧭 Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Chat", use_container_width=True):
            st.switch_page("pages/chatbot.py")
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("pages/landing.py")
    
    st.markdown("---")

# Initialize data loader
@st.cache_resource
def init_data_loader():
    """Initialize data loader with caching."""
    return ArgoDataLoader()

data_loader = init_data_loader()

# Load data
try:
    ds = data_loader.load_dataset()
    df = data_loader.get_dataframe()
    available_profiles = data_loader.get_available_profiles()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Show dataset summary
st.subheader("Dataset Info")
if ds is not None:
    st.write(ds)
else:
    st.error("Could not load dataset")
    st.stop()

# Profile selection with enhanced info
col1, col2 = st.columns([2, 1])

with col1:
    if available_profiles:
        profile_id = st.selectbox(
            "Select Profile", 
            available_profiles,
            help=f"Available profiles: {len(available_profiles)} total"
        )
    else:
        st.error("No profiles available")
        st.stop()

with col2:
    st.metric("Total Profiles", len(available_profiles))
    st.metric("Total Measurements", len(df))

# Get profile data
df_prof = data_loader.get_profile_data(profile_id)
profile_summary = data_loader.get_profile_summary(profile_id)

# Show profile summary
if "error" not in profile_summary:
    st.subheader(f"Profile {profile_id} Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📏 Data Points",
            profile_summary["measurements"]
        )
    
    with col2:
        st.metric(
            "🌊 Max Depth",
            f"{profile_summary['depth_info']['max_pressure']:.1f} dbar"
        )
    
    with col3:
        st.metric(
            "🌡️ Temp Range",
            f"{profile_summary['temperature']['min']:.1f} - {profile_summary['temperature']['max']:.1f}°C"
        )
    
    with col4:
        st.metric(
            "🧂 Salinity Range",
            f"{profile_summary['salinity']['min']:.2f} - {profile_summary['salinity']['max']:.2f} PSU"
        )
else:
    st.error(profile_summary["error"])
    st.stop()

# Show table
st.subheader(f"Profile {profile_id} Data")
if not df_prof.empty:
    # Display options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        show_all = st.checkbox("Show all data", value=False)
        if not show_all:
            n_rows = st.slider("Number of rows", 5, min(50, len(df_prof)), 20)
        else:
            n_rows = len(df_prof)
    
    # Display dataframe
    display_df = df_prof[["PRES", "TEMP", "PSAL"]].round(3)
    if show_all:
        st.dataframe(display_df, use_container_width=True)
    else:
        st.dataframe(display_df.head(n_rows), use_container_width=True)
    
    # Enhanced Plot
    st.subheader("Visualizations")
    
    # Plot options
    plot_col1, plot_col2 = st.columns(2)
    
    with plot_col1:
        plot_type = st.selectbox(
            "Plot Type",
            ["Combined Profile", "Temperature Only", "Salinity Only", "T-S Diagram"]
        )
    
    with plot_col2:
        grid_enabled = st.checkbox("Show Grid", value=True)
    
    if plot_type == "Combined Profile":
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_prof["TEMP"], df_prof["PRES"], label="Temperature (°C)", color="red", linewidth=2)
        ax.plot(df_prof["PSAL"], df_prof["PRES"], label="Salinity (PSU)", color="blue", linewidth=2)
        ax.invert_yaxis()
        ax.set_xlabel("Value")
        ax.set_ylabel("Pressure (dbar)")
        ax.set_title(f"Argo Float Profile {profile_id}")
        ax.legend()
        if grid_enabled:
            ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    elif plot_type == "Temperature Only":
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_prof["TEMP"], df_prof["PRES"], color="red", linewidth=2)
        ax.invert_yaxis()
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Pressure (dbar)")
        ax.set_title(f"Temperature Profile {profile_id}")
        if grid_enabled:
            ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    elif plot_type == "Salinity Only":
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_prof["PSAL"], df_prof["PRES"], color="blue", linewidth=2)
        ax.invert_yaxis()
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Pressure (dbar)")
        ax.set_title(f"Salinity Profile {profile_id}")
        if grid_enabled:
            ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    elif plot_type == "T-S Diagram":
        fig, ax = plt.subplots(figsize=(8, 6))
        scatter = ax.scatter(df_prof["PSAL"], df_prof["TEMP"], 
                           c=df_prof["PRES"], cmap='viridis', s=50)
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title(f"Temperature-Salinity Diagram (Profile {profile_id})")
        cbar = plt.colorbar(scatter)
        cbar.set_label("Pressure (dbar)")
        if grid_enabled:
            ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    # Additional analysis
    with st.expander("🔬 Advanced Analysis"):
        if "ocean_characteristics" in profile_summary:
            chars = profile_summary["ocean_characteristics"]
            
            st.write("**Water Mass Analysis**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("*Surface Layer*")
                surface = chars["surface_layer"]
                st.write(f"- Average Temperature: {surface['avg_temp']:.2f}°C")
                st.write(f"- Average Salinity: {surface['avg_salinity']:.2f} PSU")
                st.write(f"- Depth Range: {surface['depth_range']}")
            
            with col2:
                st.write("*Deep Layer*")
                deep = chars["deep_layer"]
                st.write(f"- Average Temperature: {deep['avg_temp']:.2f}°C")
                st.write(f"- Average Salinity: {deep['avg_salinity']:.2f} PSU")
                st.write(f"- Depth Range: {deep['depth_range']}")
            
            strat = chars["stratification"]
            st.write("**Stratification**")
            st.write(f"- Temperature Difference: {strat['temperature_difference']:.2f}°C")
            st.write(f"- Stratification: {strat['stratification_strength'].title()}")
            
            # Gradients
            st.write("**Gradients**")
            st.write(f"- Temperature Gradient: {profile_summary['temperature']['gradient']:.4f} °C/dbar")
            st.write(f"- Salinity Gradient: {profile_summary['salinity']['gradient']:.4f} PSU/dbar")
else:
    st.warning(f"No data available for profile {profile_id}")