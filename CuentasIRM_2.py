import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

st.set_page_config(page_title="Gestor Gastos", layout="wide")

# Conexión nativa
conn = st.connection("postgresql", type="sql")

def inicializar_db():
    try:
        with conn.session as session:
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
            return True
    except Exception as e:
        # ESTO ES CLAVE: Mostramos el error real para diagnosticar
        st.error(f"❌ Error Técnico Real: {e}")
        return False

st.title("💰 Control de Gastos")

if st.button("🔌 Probar Conexión ahora"):
    if inicializar_db():
        st.success("¡Conexión exitosa a Supabase!")
    else:
        st.error("La conexión sigue fallando.")

# El resto del código de pestañas (tab1, tab2) igual que el anterior...
