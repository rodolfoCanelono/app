import os
from sqlalchemy import create_engine, text
import streamlit as st

conn_url = os.environ["DB_URL"]

st.write("URL final:", repr(conn_url))

engine = create_engine(conn_url)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa")
except Exception as e:
    st.error(f"Error de conexión: {e}")
