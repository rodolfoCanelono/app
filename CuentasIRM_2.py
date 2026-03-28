import streamlit as st
from sqlalchemy import create_engine, text

# String de conexión directo al pooler
conn_url = "postgresql://postgres:Maniclo-2026@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

st.write("URL final limpia:", repr(conn_url))

engine = create_engine(conn_url)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa a Supabase")
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
