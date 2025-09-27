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
