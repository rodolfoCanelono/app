import streamlit as st
from sqlalchemy import create_engine, text

# --- Leer secretos separados ---
s = st.secrets["connections"]["postgresql"]

# Mostrar valores (excepto contraseña) para debug
st.write("🔹 Conexión a Supabase")
st.write("User:", s['user'])
st.write("Host:", s['host'])
st.write("Port:", s['port'])
st.write("DB Name:", s['dbname'])
st.write("SSL Mode:", s['sslmode'])
st.write("Password: 🔒 Oculta")

# --- Concatenar manualmente cada parte para armar la URL ---
conn_url = (
    "postgresql://"
    + s['user'] + ":" + s['password']
    + "@" + s['host'] + ":" + s['port']
    + "/" + s['dbname']
    + "?sslmode=" + s['sslmode']
)

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
