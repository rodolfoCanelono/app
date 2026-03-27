import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

st.set_page_config(page_title="Gestor Gastos ICCI", layout="wide")

# Conexión nativa de Streamlit
conn = st.connection("postgresql", type="sql")

st.title("💰 Control de Gastos Hogar")

# --- ZONA DE DIAGNÓSTICO ---
with st.expander("🛠 Configuración de Base de Datos"):
    if st.button("Verificar Conexión y Crear Tabla"):
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
                st.success("✅ Conexión establecida y tabla verificada.")
        except Exception as e:
            st.error(f"❌ Error al conectar: {e}")

st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gasto", "📊 Dashboard"])

with tab1:
    with st.form("registro_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            con = st.selectbox("Concepto", ["Comida", "Cuentas", "Hipotecario", "Salud", "Otros"])
            mon = st.number_input("Monto ($)", min_value=0, step=1000)
        with col2:
            fec = st.date_input("Fecha", datetime.now())
            res = st.selectbox("Responsable", ["Rodolfo", "Irisysleyer", "Machulon"])
        
        if st.form_submit_button("Guardar Gasto"):
            try:
                with conn.session as session:
                    session.execute(
                        text("INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) VALUES (:f, :c, :m, :r)"),
                        {"f": fec, "c": con, "m": mon, "r": res}
                    )
                    session.commit()
                st.success("✅ Gasto guardado.")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

with tab2:
    if st.button("🔄 Cargar Datos"):
        try:
            df = conn.query("SELECT * FROM gastos_hogar ORDER BY fecha DESC", ttl=0)
            if not df.empty:
                st.metric("Total Acumulado", f"${df['monto'].sum():,.0f}")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay datos registrados aún.")
        except Exception as e:
            st.error(f"Error al leer: {e}")
