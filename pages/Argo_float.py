import streamlit as st
from datetime import datetime
import pandas as pd

from utils.query_utils import fetch_argo_data
from visualization.plot_profiles import plot_vertical_profiles
from visualization.plot_time_series import plot_time_series
from visualization.plot_map import plot_float_path
from visualization.plot_heatmap import plot_correlation_heatmap

st.set_page_config(page_title="Argo Float Dashboard", layout="wide")
st.title("🌊 Argo Float Data Visualization Dashboard")

# -----------------------------
# 1️⃣ Filter Controls in Main Window
# -----------------------------
st.header("Filter Options")

# Platform selection
all_floats = fetch_argo_data()[["platform_number"]].drop_duplicates().sort_values("platform_number")
selected_float = st.selectbox("Select Platform Number", all_floats["platform_number"].tolist())

# Date range selection
min_date = fetch_argo_data(platform_number=selected_float)["juld"].min()
max_date = fetch_argo_data(platform_number=selected_float)["juld"].max()
start_date, end_date = st.date_input("Select Date Range",
                                     value=(min_date.date(), max_date.date()),
                                     min_value=min_date.date(),
                                     max_value=max_date.date())
start_ts = datetime.combine(start_date, datetime.min.time())  # start of day
end_ts = datetime.combine(end_date, datetime.max.time())

# Depth/Pressure range slider
df_temp = fetch_argo_data(platform_number=selected_float,
                          start_date=start_ts,
                          end_date=end_ts)
df_temp["pres"] = pd.to_numeric(df_temp["pres"], errors="coerce")
df_temp = df_temp.dropna(subset=["pres"])
if df_temp.empty:
    st.warning("⚠️ No pressure data available for the selected float/date range.")
    st.stop()
min_pres = df_temp["pres"].min()
max_pres = df_temp["pres"].max()
depth_range = st.slider("Select Pressure Range (Depth)", 
                        float(min_pres), float(max_pres), (float(min_pres), float(max_pres)))

# -----------------------------
# 2️⃣ Fetch Filtered Data (on-demand)
# -----------------------------
@st.cache_data
def get_filtered_data(platform, start, end, pres_range):
    df = fetch_argo_data(platform_number=platform, start_date=start, end_date=end)
    df["pres"] = pd.to_numeric(df["pres"], errors="coerce")
    df = df.dropna(subset=["pres"])  
    df_filtered = df_temp[(df_temp["pres"] >= depth_range[0]) & (df_temp["pres"] <= depth_range[1])]
    return df_filtered

df = get_filtered_data(selected_float, start_date, end_date, depth_range)

if df.empty:
    st.warning("⚠️ No data found for the selected filters.")
    st.stop()

st.success(f"✅ Loaded {len(df)} rows for Platform {selected_float}")

# -----------------------------
# 3️⃣ Float Path Map
# -----------------------------
st.header("🌍 Float Path Map")
fig_map = plot_float_path(df)
st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# 4️⃣ Vertical Profiles (Depth vs Temp/Salinity)
# -----------------------------
st.header("📊 Vertical Profiles")
fig_profiles = plot_vertical_profiles(df)
st.pyplot(fig_profiles)

# -----------------------------
# 5️⃣ Temperature-Salinity (T-S) Diagram
# -----------------------------
st.header("📈 Temperature-Salinity (T-S) Diagram")
fig_ts = plot_vertical_profiles(df)  # You can create a dedicated T-S function; placeholder for now
st.pyplot(fig_ts)

# -----------------------------
# 6️⃣ Time Series
# -----------------------------
st.header("⏱️ Time Series")
fig_temp, fig_psal = plot_time_series(df)
st.plotly_chart(fig_temp, use_container_width=True)
st.plotly_chart(fig_psal, use_container_width=True)

# -----------------------------
# 7️⃣ Correlation Heatmap
# -----------------------------
st.header("🔥 Correlation Analysis")
fig_corr = plot_correlation_heatmap(df)
st.pyplot(fig_corr)
