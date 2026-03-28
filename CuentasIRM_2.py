from sqlalchemy import create_engine, text
import streamlit as st

# Leer el secret (puede tener saltos de línea)
conn_url_raw = st.secrets["connections"]["postgresql"]["url"]

# 🔥 Limpiar saltos de línea y espacios invisibles
conn_url = "".join(conn_url_raw.split())

st.write("URL final limpia:", repr(conn_url))

# Crear engine
engine = create_engine(conn_url)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa")
except Exception as e:
    st.error(f"Error de conexión: {e}")
