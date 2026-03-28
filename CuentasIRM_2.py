import streamlit as st
import socket
from sqlalchemy import create_engine, text
# --- Leer secretos separados ---
s = st.secrets["connections"]["postgresql"]

user = s['user'].replace("\n","").strip()
password = 'Maniclo-2026'.replace("\n","").strip()
host = s['host'].replace("\n","").strip()
port = s['port'].replace("\n","").strip()
dbname = s['dbname'].replace("\n","").strip()
sslmode = s['sslmode'].replace("\n","").strip()
tira="postgresql://postgres:Maniclo-2026@db.oldbexdvxquhbtpchqwe.supabase.co:5432/postgres"

st.write("mi tira:",repr(tira))
conn_url = tira
# --- Concatenar URL ---
#conn_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"

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
