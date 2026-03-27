import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

st.set_page_config(page_title="Gestor Gastos", layout="wide")

# Conexión nativa usando el URL de los Secrets
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
    except Exception as e:
        st.sidebar.error("Error de conexión. Revisa los Secrets.")

# Intentar crear tabla
inicializar_db()

st.title("💰 Control de Gastos")

tab1, tab2 = st.tabs(["📝 Registro", "📊 Reporte"])

with tab1:
    with st.form("f1", clear_on_submit=True):
        c1, c2 = st.columns(2)
        con = c1.selectbox("Concepto", ["Comida", "Universidad", "Medicinas", "Hipotecario", "Otros"])
        mon = c1.number_input("Monto", min_value=0, step=1000)
        fec = c2.date_input("Fecha", datetime.now())
        res = c2.selectbox("Responsable", ["Rodolfo", "Irisysleyer", "Machulon"])
        
        if st.form_submit_button("Guardar"):
            with conn.session as session:
                session.execute(text("INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) VALUES (:f, :c, :m, :r)"),
                                {"f": fec, "c": con, "m": mon, "r": res})
                session.commit()
            st.success("Guardado")
            st.rerun()

with tab2:
    try:
        df = conn.query("SELECT * FROM gastos_hogar ORDER BY fecha DESC", ttl=0)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.metric("Total", f"${df['monto'].sum():,.0f}")
        else:
            st.info("No hay datos.")
    except:
        st.error("Error al cargar datos.")
