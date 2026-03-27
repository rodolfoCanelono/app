import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
import os
st.write("DATABASE_URL env var:", os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Gastos Hogar", layout="wide")

# Conexión nativa de Streamlit (Lee de los Secrets)
conn = st.connection("postgresql", type="sql")
st.write("Conexión actual:", conn)

st.title("💰 Control de Gastos del Hogar")

# --- VERIFICACIÓN INICIAL ---
if st.button("🔌 Verificar Conexión"):
    try:
        with conn.session as session:
            session.execute(text("SELECT 1"))
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
            st.success("✅ ¡Conectado con éxito a Supabase!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registro", "📊 Reporte"])

with tab1:
    with st.form("form_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        con = c1.selectbox("Concepto", ["Comida", "Cuentas", "Hipotecario", "Salud", "Otros"])
        mon = c1.number_input("Monto ($)", min_value=0, step=1000)
        fec = c2.date_input("Fecha", datetime.now())
        res = c2.selectbox("Responsable", ["Rodolfo", "Irisysleyer", "Machulon"])
        
        if st.form_submit_button("Guardar"):
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
    if st.button("🔄 Cargar/Actualizar Datos"):
        try:
            df = conn.query("SELECT * FROM gastos_hogar ORDER BY fecha DESC", ttl=0)
            if not df.empty:
                st.metric("Total Acumulado", f"${df['monto'].sum():,.0f}")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay datos registrados aún.")
        except Exception as e:
            st.error(f"Error al leer datos: {e}")
