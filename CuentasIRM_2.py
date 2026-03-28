import streamlit as st
from sqlalchemy import create_engine, text

# --- Leer secretos separados ---
s = st.secrets["connections"]["postgresql"]

# Mostrar valores (para verificar, opcional)
st.write("🔹 Conexión a Supabase")
st.write("User:", s['user'])
st.write("Host:", s['host'])
st.write("Port:", s['port'])
st.write("DB Name:", s['dbname'])
st.write("SSL Mode:", s['sslmode'])
# ⚠️ No mostramos la contraseña directamente en producción
st.write("Password: 🔒 Oculta")

# --- Construir URL de conexión limpia ---
# Esto elimina saltos de línea o espacios invisibles
conn_url = f"postgresql://{s['user']}:{s['password']}@{s['host']}:{s['port']}/{s['dbname']}?sslmode={s['sslmode']}"
conn_url = "".join(conn_url.split())  # elimina saltos de línea invisibles

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
