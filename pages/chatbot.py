import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd

st.title("🤖 Chat with Argo Data")

# Load dataset
@st.cache_data
def load_data():
    ds = xr.open_dataset("data/20250101_prof.nc")
    return ds

ds = load_data()
df = ds[["PRES", "TEMP", "PSAL"]].to_dataframe().reset_index()

# Input query
query = st.text_input("Ask a question about the data", "")

if query:
    st.write(f"🔎 You asked: {query}")

    # --- Prototype logic (simulate ML pipeline) ---
    if "temperature" in query.lower():
        profile_id = 0
        df_prof = df[df["N_PROF"] == profile_id]

        fig, ax = plt.subplots(figsize=(6,5))
        ax.plot(df_prof["TEMP"], df_prof["PRES"], label="Temperature (°C)", color="blue")
        ax.invert_yaxis()
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Pressure (dbar)")
        ax.set_title(f"Temperature Profile (Profile {profile_id})")
        ax.legend()
        st.pyplot(fig)

    elif "salinity" in query.lower():
        profile_id = 0
        df_prof = df[df["N_PROF"] == profile_id]

        fig, ax = plt.subplots(figsize=(6,5))
        ax.plot(df_prof["PSAL"], df_prof["PRES"], label="Salinity (PSU)", color="orange")
        ax.invert_yaxis()
        ax.set_xlabel("Salinity (PSU)")
        ax.set_ylabel("Pressure (dbar)")
        ax.set_title(f"Salinity Profile (Profile {profile_id})")
        ax.legend()
        st.pyplot(fig)

    else:
        st.warning("⚠️ Prototype: I only understand 'temperature' or 'salinity' queries right now.")
