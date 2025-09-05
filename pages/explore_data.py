import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd

st.title("📊 Explore Argo Data")

# Load dataset
@st.cache_data
def load_data():
    ds = xr.open_dataset("data/20250101_prof.nc")
    return ds

ds = load_data()

# Show dataset summary
st.subheader("Dataset Info")
st.write(ds)

# Convert to dataframe
df = ds[["PRES", "TEMP", "PSAL"]].to_dataframe().reset_index()

# Select profile
profile_id = st.selectbox("Select Profile", df["N_PROF"].unique())
df_prof = df[df["N_PROF"] == profile_id]

# Show table
st.subheader(f"Profile {profile_id} Data")
st.dataframe(df_prof.head(20))

# Plot
fig, ax = plt.subplots(figsize=(6,5))
ax.plot(df_prof["TEMP"], df_prof["PRES"], label="Temperature (°C)")
ax.plot(df_prof["PSAL"], df_prof["PRES"], label="Salinity (PSU)")
ax.invert_yaxis()
ax.set_xlabel("Value")
ax.set_ylabel("Pressure (dbar)")
ax.set_title(f"Argo Float Profile {profile_id}")
ax.legend()
st.pyplot(fig)
