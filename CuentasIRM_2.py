import streamlit as st
from sqlalchemy import create_engine, text

# --- Leer secretos separados ---
s = st.secrets["connections"]["postgresql"]
# Limpiar espacios y saltos de línea
user = s['user'].strip()
password = s['password'].strip()
host = s['host'].strip()
port = s['port'].strip()
dbname = s['dbname'].strip()
sslmode = s['sslmode'].strip()

conn_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
st.write("URL final limpia:", repr(conn_url))  # Para debug

# --- Crear engine de SQLAlchemy ---
engine = create_engine(conn_url)

# --- Verificar conexión ---
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa a Supabase")
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
