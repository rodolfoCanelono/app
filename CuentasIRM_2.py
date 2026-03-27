import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from sqlalchemy import text

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Gastos - Supabase", layout="wide")

# 2. Conexión nativa (usa los Secrets configurados arriba)
conn = st.connection("postgresql", type="sql")

# 3. Listas
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = ["Comida", "Universidad Max", "Medicinas", "Ropa Max", "Regalos", "Enseres", "Gastos Comunes", "Hipotecario"]

# 4. Funciones
def inicializar_db():
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

def guardar_gasto(f, c, m, r):
    with conn.session as session:
        query = text("INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) VALUES (:f, :c, :m, :r)")
        session.execute(query, {"f": f, "c": c, "m": m, "r": r})
        session.commit()

# Ejecución
inicializar_db()

st.title("💰 Gestor de Gastos (Nativa)")

tab1, tab2 = st.tabs(["📝 Registro", "📊 Dashboard"])

with tab1:
    with st.form("nuevo_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con = st.selectbox("Concepto", LISTA_CONCEPTOS)
            mon = st.number_input("Monto", min_value=0, step=1000)
        with c2:
            fec = st.date_input("Fecha", datetime.now())
            res = st.selectbox("Responsable", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            guardar_gasto(fec, con, mon, res)
            st.success("✅ Guardado")
            st.rerun()

with tab2:
    # conn.query maneja automáticamente la conversión a DataFrame
    df = conn.query("SELECT * FROM gastos_hogar", ttl=0)
    
    if not df.empty:
        st.metric("Total Acumulado", f"${df['monto'].sum():,.0f}")
        st.dataframe(df, use_container_width=True)
        
        fig = px.pie(df, values='monto', names='concepto', title="Distribución por Concepto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos todavía.")
