import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client

# 1. Configuración de la aplicación
st.set_page_config(
    page_title="Gestor de Gastos ICCI - Supabase",
    page_icon="💰",
    layout="wide" 
)

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Se obtienen las variables desde el entorno o secrets de Streamlit
url: str = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("Faltan las credenciales de Supabase. Configúralas en los Secrets de Streamlit.")
    st.stop()

supabase: Client = create_client(url, key)

# --- LISTAS DE SELECCIÓN ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_datos_db():
    """Consulta todos los datos desde la tabla de Supabase"""
    try:
        # Realiza la consulta a la tabla 'gastos_hogar'
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable):
    """Inserta un nuevo registro en Supabase"""
    nuevo_gasto = {
        "fecha": fecha.strftime("%Y-%m-%d"), # Convertir fecha a string para JSON
        "concepto": concepto,
        "monto": monto,
        "responsable": responsable
    }
    try:
        supabase.table("gastos_hogar").insert(nuevo_gasto).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- INTERFAZ DE STREAMLIT ---

st.title("📊 Gastos del Hogar (Supabase)")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
    
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("¿Monto del Gasto?", min_value=1000, step=1000)
   
        with col_reg2:
            fecha_in = st.date_input("¿Fecha del gasto?", datetime.now())
            responsable_in = st.selectbox("¿Quién realizó el gasto?", LISTA_RESPONSABLES)
        
        boton_guardar = st.form_submit_button("Guardar Gasto")

    if boton_guardar:
        if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in):
            st.success(f"✅ Registrado en Supabase: {concepto_in}")
            st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos_db()

    if not df.empty:
        # Asegurar formato de fecha
        df['fecha'] = pd.to_datetime(df['fecha'])

        st.subheader("🔍 Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            inicio = st.date_input("Desde", df['fecha'].min().date())
        with col_f2:
            fin = st.date_input("Hasta", df['fecha'].max().date())
        with col_f3:
            quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
        with col_f4:
            que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS)

        # Lógica de Filtrado en Pandas
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos":
            mask = mask & (df['responsable'] == quien)
        if que_gasto != "Todos":
            mask = mask & (df['concepto'] == que_gasto)
        
        df_filtrado = df.loc[mask]

        # --- SECCIÓN DE PAGOS ---
        st.markdown("---")
        total_filtrado = df_filtrado['monto'].sum()
        mitad = total_filtrado / 2
        
        st.write("⚖️ **División de Gastos (Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total General", f"${total_filtrado:,.0f}")

        # --- GRÁFICAS ---
        st.markdown("---")
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            gastos_concepto = df_filtrado.groupby('concepto')['monto'].sum().reset_index()
            fig = px.pie(gastos_concepto, values='monto', names='concepto', hole=0.4, title="Por Concepto")
            st.plotly_chart(fig, use_container_width=True)

        with col_graf2:
            gastos_persona = df_filtrado.groupby('responsable')['monto'].sum().reset_index()
            fig = px.pie(gastos_persona, values='monto', names='responsable', hole=0.4, title="Por Responsable")
            st.plotly_chart(fig, use_container_width=True)

        # --- TABLA ---
        st.markdown("---")
        df_display = df_filtrado.copy().sort_values(by='fecha', ascending=False)
        df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

st.sidebar.markdown("### Configuración")
st.sidebar.success("Conectado a Supabase")
