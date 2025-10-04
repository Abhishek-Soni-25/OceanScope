from db_connection import get_connection
import psycopg2

# -----------------------------
# SCHEMA DICTIONARY
# Add all tables here
# -----------------------------
SCHEMA = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(256) NOT NULL
        );
    """,

    # -----------------------------
    # ARGO TABLE
    # -----------------------------
    "argo_data": """
        CREATE TABLE IF NOT EXISTS argo_data (
            id SERIAL PRIMARY KEY,
            platform_number VARCHAR(20),
            cycle_number FLOAT,
            juld TIMESTAMP,
            latitude FLOAT,
            longitude FLOAT,
            pres FLOAT,
            temp FLOAT,
            psal FLOAT,
            n_prof INT,
            n_levels INT
        );
    """,

    # -----------------------------
    # BGC TABLE
    # -----------------------------
    "bgc_data": """
        CREATE TABLE IF NOT EXISTS bgc_data (
            id SERIAL PRIMARY KEY,
            platform_number VARCHAR(20),
            cycle_number FLOAT,
            juld TIMESTAMP,
            latitude FLOAT,
            longitude FLOAT,
            pres FLOAT,
            temp FLOAT,
            psal FLOAT,
            pres_adjusted FLOAT,
            temp_adjusted FLOAT,
            psal_adjusted FLOAT,
            ph_in_situ_total FLOAT,
            doxy FLOAT,
            nitrate FLOAT,
            chla FLOAT,
            bbp700 FLOAT,
            n_prof INT,
            n_levels INT
        );
    """,

    # -----------------------------
    # SST TABLE
    # -----------------------------
    "sst_data": """
        CREATE TABLE IF NOT EXISTS sst_data (
            id SERIAL PRIMARY KEY,
            time TIMESTAMP,
            latitude FLOAT,
            longitude FLOAT,
            sea_surface_temperature FLOAT,
            wind_speed FLOAT,
            sea_ice_fraction FLOAT
        );
    """
}

# -----------------------------
# FUNCTION TO CREATE TABLES
# -----------------------------
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for table_name, ddl in SCHEMA.items():
            print(f"Checking table '{table_name}'...")
            cursor.execute(ddl)
            print(f"✅ Table '{table_name}' ready")
        conn.commit()
        print("🎉 All tables are created or already exist")
    except psycopg2.Error as e:
        print("❌ Error creating tables:", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    create_tables()
