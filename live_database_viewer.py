# live_database_viewer.py

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="db_refresh")

# ---------------------------- #
# PostgreSQL Database Settings #
# ---------------------------- #
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "societysync"
DB_USER = "postgres"
DB_PASSWORD = "durgeshvs1610"

# ---------------------------- #
# Connect to Database          #
# ---------------------------- #
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

conn = get_connection()

# ---------------------------- #
# Get All Tables in Database   #
# ---------------------------- #
def get_tables():
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
        """)
        return [row[0] for row in cursor.fetchall()]

# ---------------------------- #
# Get Columns of a Table       #
# ---------------------------- #
def get_columns(table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        return [row[0] for row in cursor.fetchall()]

# ---------------------------- #
# Fetch Table Data             #
# ---------------------------- #
def fetch_table_data(table_name):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT 100;")
        data = cursor.fetchall()
    return pd.DataFrame(data)

# ---------------------------- #
# Streamlit UI                 #
# ---------------------------- #
st.set_page_config(page_title="Live Database Viewer", layout="wide")
st.title("🖥️ Live Database Viewer")

tables = get_tables()
selected_table = st.selectbox("Select Table", tables)

if selected_table:
    st.subheader(f"Table: {selected_table}")
    data = fetch_table_data(selected_table)
    
    if not data.empty:
        st.dataframe(data, use_container_width=True)
        st.info(f"Showing latest {len(data)} rows. Auto-refresh every 5 seconds.")
    else:
        st.warning("Table is empty.")
    
    columns = get_columns(selected_table)
    col1 = columns[0] if len(columns) >= 1 else None
    col2 = columns[1] if len(columns) >= 2 else None

    # ---------------------------- #
    # Versatile Query Suggestions  #
    # ---------------------------- #
    versatile_queries = {}
    if col1 and col2:
        versatile_queries = {
            "Show all rows": f"SELECT * FROM {selected_table} LIMIT 100;",
            "Count rows": f"SELECT COUNT(*) FROM {selected_table};",
            "Last 10 entries": f"SELECT * FROM {selected_table} ORDER BY {col1} DESC LIMIT 10;",
            f"Select first two columns ({col1}, {col2})": f"SELECT {col1}, {col2} FROM {selected_table} LIMIT 50;",
            f"Order by first column ({col1}) asc": f"SELECT * FROM {selected_table} ORDER BY {col1} ASC LIMIT 50;",
            f"Order by first column ({col1}) desc": f"SELECT * FROM {selected_table} ORDER BY {col1} DESC LIMIT 50;",
            f"Select distinct first column ({col1})": f"SELECT DISTINCT {col1} FROM {selected_table} LIMIT 50;",
            f"Top 5 by second column ({col2})": f"SELECT * FROM {selected_table} ORDER BY {col2} DESC LIMIT 5;",
            f"Where first column ({col1}) not null": f"SELECT * FROM {selected_table} WHERE {col1} IS NOT NULL LIMIT 50;",
            f"Aggregate example (COUNT by {col1})": f"SELECT {col1}, COUNT(*) FROM {selected_table} GROUP BY {col1} LIMIT 50;"
        }

# ---------------------------- #
# Run Custom SQL Query          #
# ---------------------------- #
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = pd.DataFrame()

with st.expander("Run Custom SQL Query"):
    st.write("💡 Basic Query Suggestions:")
    for name, q in versatile_queries.items():
        st.code(q)

    query = st.text_area("Enter SQL Query", value=st.session_state.last_query, height=150)
    
    if st.button("Execute Query"):
        if not query.strip():
            st.warning("Please enter a query to execute.")
        else:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query)
                    # Commit if query modifies data
                    if query.strip().lower().startswith(("insert", "update", "delete", "create", "alter", "drop")):
                        conn.commit()
                    # Fetch results for SELECT
                    if cursor.description:
                        result = cursor.fetchall()
                        df_result = pd.DataFrame(result)
                        st.session_state.last_result = df_result
                    else:
                        st.session_state.last_result = pd.DataFrame()
                st.session_state.last_query = query
                st.success("Query executed successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"Error: {e}")

    # Show last results persistently
    if not st.session_state.last_result.empty:
        st.subheader("Query Results")
        st.dataframe(st.session_state.last_result, use_container_width=True)
