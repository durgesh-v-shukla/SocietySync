import os
import psycopg2

conn_str = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(conn_str)
    print("Connected successfully!")
    conn.close()
except Exception as e:
    print("Connection failed:", e)
