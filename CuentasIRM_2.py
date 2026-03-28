import os
from sqlalchemy import create_engine, text
import streamlit as st
s = st.secrets["connections"]["postgresql"]
PRINT('user' ,s[user],'password ', s[password],'host ', s[host],'dbname ',s['dbname'],'sslmode ',s['sslmode'])
conn_url = f"postgresql://{s['user']}:{s['password']}@{s['host']}:{s['port']}/{s['dbname']}?sslmode={s['sslmode']}"

st.write("URL final:", repr(conn_url))
engine = create_engine(conn_url)
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        st.success("✅ Conexión exitosa")
except Exception as e:
    st.error(f"Error de conexión: {e}")
