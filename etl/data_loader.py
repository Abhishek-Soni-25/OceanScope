import os
import pandas as pd
import xarray as xr
import numpy as np
from db_setup.db_connection import get_connection
from etl.utils import delete_file


# --------------------------------
# Column Mapping (File → DB)
# --------------------------------
COLUMN_MAPPING = {
    "argo_data": {
        "PLATFORM_NUMBER": "platform_number",
        "CYCLE_NUMBER": "cycle_number",
        "JULD": "juld",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "PRES": "pres",
        "TEMP": "temp",
        "PSAL": "psal",
        "N_PROF": "n_prof",
        "N_LEVELS": "n_levels"
    },
    "bgc_data": {
        "PLATFORM_NUMBER": "platform_number",
        "CYCLE_NUMBER": "cycle_number",
        "JULD": "juld",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "PRES": "pres",
        "TEMP": "temp",
        "PSAL": "psal",
        "PRES_ADJUSTED": "pres_adjusted",
        "TEMP_ADJUSTED": "temp_adjusted",
        "PSAL_ADJUSTED": "psal_adjusted",
        "PH_IN_SITU_TOTAL": "ph_in_situ_total",
        "DOXY": "doxy",
        "CHLA": "chla",
        "BBP700": "bbp700",
        "N_PROF": "n_prof",
        "N_LEVELS": "n_levels"
    },
    "sst_data": {
        "time": "time",
        "lat": "latitude",
        "lon": "longitude",
        "sea_surface_temperature": "sea_surface_temperature",
        "wind_speed": "wind_speed",
        "sea_ice_fraction": "sea_ice_fraction"
    }
}


# --------------------------------
# Helper
# --------------------------------
def normalize_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Rename columns based on predefined mapping"""
    mapping = COLUMN_MAPPING[table_name]
    df = df.rename(columns={col: mapping[col] for col in df.columns if col in mapping})
    return df


# --------------------------------
# Load NetCDF → DB
# --------------------------------
def load_nc_to_db(file_path: str, table_name: str, logger):
    try:
        # 1. Read NetCDF into DataFrame
        ds = xr.open_dataset(file_path)

        # 2. Process Argo/BGC data
        if table_name in ["argo_data", "bgc_data"]:
            n_prof = ds.dims['N_PROF']
            n_levels = ds.dims['N_LEVELS']

            df_dict = {}
            mapping = COLUMN_MAPPING[table_name]

            # Profile index repeated for each level
            df_dict["n_prof"] = np.repeat(np.arange(n_prof), n_levels)

            # Level index tiled across profiles
            df_dict["n_levels"] = np.tile(np.arange(n_levels), n_prof)

            # Build columns
            for nc_col, df_col in mapping.items():
                if nc_col in ds:
                    dims = ds[nc_col].dims
                    if dims == ('N_PROF',):
                        df_dict[df_col] = ds[nc_col].values.repeat(n_levels)
                    elif dims == ('N_PROF', 'N_LEVELS'):
                        df_dict[df_col] = ds[nc_col].values.flatten()
                    else:
                        df_dict[df_col] = ds[nc_col].values.flatten()

            df = pd.DataFrame(df_dict)

            # Decode PLATFORM_NUMBER if it contains byte strings
            if "platform_number" in df.columns:
                df["platform_number"] = df["platform_number"].apply(
                    lambda x: x.decode("utf-8").strip() if isinstance(x, (bytes, bytearray)) else x
                )

        # 3. Process SST data
        elif table_name == "sst_data":
            # Select only required variables
            vars_needed = list(COLUMN_MAPPING[table_name].keys())
            ds_sel = ds[vars_needed]

            # Convert to DataFrame
            df = ds_sel.to_dataframe().reset_index()

            # Normalize column names
            df = normalize_columns(df, table_name)

            # Keep only mapped columns
            valid_cols = list(COLUMN_MAPPING[table_name].values())
            df = df[valid_cols]

            # Drop rows where all key vars are NaN
            df = df.dropna(subset=["sea_surface_temperature", "wind_speed", "sea_ice_fraction"])

        else:
            logger.warning(f"Unknown table: {table_name}")
            return        

        if df.empty:
            logger.warning(f"No valid columns found in {file_path} for {table_name}")
            return

        # 5. Insert into DB
        conn = get_connection()
        cursor = conn.cursor()

        valid_cols = list(COLUMN_MAPPING[table_name].values())
        df = df[valid_cols] 

        placeholders = ", ".join(["%s"] * len(valid_cols))
        sql = f"INSERT INTO {table_name} ({', '.join(valid_cols)}) VALUES ({placeholders})"

        for _, row in df.iterrows():
            cursor.execute(sql, tuple(row.values))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Loaded {len(df)} rows into {table_name} from {os.path.basename(file_path)}")

        # 6. Delete file after processing
        ds.close()
        delete_file(file_path, logger)

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
