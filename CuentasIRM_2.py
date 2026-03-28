from sqlalchemy import create_engine
import streamlit as st

conn_url = st.secrets["connections"]["postgresql"]["url"]
engine = create_engine(conn_url)
st.write(repr(conn_url))
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        st.success("✅ Conexión exitosa")
except Exception as e:
    st.error(f"Error de conexión: {e}")
