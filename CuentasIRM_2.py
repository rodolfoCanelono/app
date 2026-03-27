import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

st.set_page_config(page_title="Gestor Gastos", layout="wide")

# Forzamos a Streamlit a olvidar conexiones fallidas anteriores
st.cache_resource.clear()

# Conexión nativa
conn = st.connection("postgresql", type="sql")

st.title("💰 Control de Gastos")

if st.button("🔌 Verificar Conexión"):
    try:
        with conn.session as session:
            # Una consulta simple para probar la tubería
            session.execute(text("SELECT 1"))
            
            # Crear la tabla si no existe
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS gastos_hogar (
                    id SERIAL PRIMARY KEY,
                    fecha DATE NOT NULL,
                    concepto TEXT NOT NULL,
                    monto FLOAT NOT NULL,
                    responsable TEXT NOT NULL
                );
            """))
            session.commit()
            st.success("✅ ¡CONECTADO! La red IPv4 y las credenciales están OK.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ... resto del código de registro y dashboard ...
