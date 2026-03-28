from sqlalchemy import create_engine, text
import streamlit as st

conn_url = st.secrets["connections"]["postgresql"]["url"]
conn_url = "".join(conn_url.split())

st.write("URL limpia:", repr(conn_url))

engine = create_engine(conn_url)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa")
except Exception as e:
    st.error(f"Error de conexión: {e}")
