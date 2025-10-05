import pandas as pd
from db_setup.db_connection import get_connection

def fetch_argo_data(platform_number=None, start_date=None, end_date=None):
    conn = get_connection()
    query = "SELECT * FROM argo_data WHERE TRUE"
    params = []
    if platform_number:
        query += " AND TRIM(platform_number) = %s"
        params.append(str(platform_number).strip())
    if start_date:
        query += " AND juld >= %s"
        params.append(start_date)
    if end_date:
        query += " AND juld <= %s"
        params.append(end_date)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df
