import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# Cargar la imagen
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(
        page_title="Gestor de Gastos - Rodolfo Canelón",
        page_icon=img_icono,
        layout="wide" 
    )
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# --- CONFIGURACIÓN DE CONEXIÓN ---
url: str = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("Faltan las credenciales de Supabase.")
    st.stop()

supabase: Client = create_client(url, key)

# --- LISTAS DE SELECCIÓN ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito"] # <-- Nueva lista
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_datos_db():
    try:
        # Se agrega "forma_pago" al SELECT
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable, forma_pago").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo_gasto = {
        "fecha": fecha.strftime("%Y-%m-%d"),
        "concepto": concepto,
        "monto": monto,
        "responsable": responsable,
        "forma_pago": forma_pago  # <-- Nuevo campo para insertar
    }
    try:
        supabase.table("gastos_hogar").insert(nuevo_gasto).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- INTERFAZ DE STREAMLIT ---
st.title("📊 Gestión de Gastos del Hogar")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
    
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("¿Monto del Gasto?", min_value=1000, step=2000, format="%d")
            forma_pago_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO) # <-- Input nuevo
   
        with col_reg2:
            fecha_in = st.date_input("¿Fecha del gasto?", datetime.now())
            responsable_in = st.selectbox("¿Quién realizó el gasto?", LISTA_RESPONSABLES)
        
        boton_guardar = st.form_submit_button("Guardar Gasto")

    if boton_guardar:
        if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in, forma_pago_in):
            st.success(f"✅ Registrado: {concepto_in} pagado con {forma_pago_in}")
            st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos_db()

    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])

        st.subheader("🔍 Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5) # Se añade una columna más
        
        with col_f1:
            inicio = st.date_input("Desde", df['fecha'].min().date())
        with col_f2:
            fin = st.date_input("Hasta", df['fecha'].max().date())
        with col_f3:
            quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
        with col_f4:
            que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS)
        with col_f5:
            como_pago = st.selectbox("Forma de Pago", ["Todos"] + LISTA_FORMAS_PAGO)

        # Lógica de Filtrado
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos":
            mask = mask & (df['responsable'] == quien)
        if que_gasto != "Todos":
            mask = mask & (df['concepto'] == que_gasto)
        if como_pago != "Todos":
            mask = mask & (df['forma_pago'] == como_pago) # <-- Filtro nuevo
        
        df_filtrado = df.loc[mask]

        # --- SECCIÓN DE PAGOS Y GRÁFICAS ---
        total_filtrado = df_filtrado['monto'].sum()
        st.metric("Total General Filtrado", f"${total_filtrado:,.0f}")

        st.markdown("---")
        col_graf1, col_graf2, col_graf3 = st.columns(3) # Tres gráficos ahora
        
        with col_graf1:
            temp_df = df_filtrado.groupby('concepto')['monto'].sum().reset_index()
            st.plotly_chart(px.pie(temp_df, values='monto', names='concepto', title="Por Concepto", hole=0.4), use_container_width=True)

        with col_graf2:
            temp_df = df_filtrado.groupby('responsable')['monto'].sum().reset_index()
            st.plotly_chart(px.pie(temp_df, values='monto', names='responsable', title="Por Responsable", hole=0.4), use_container_width=True)

        with col_graf3:
            # --- NUEVA GRÁFICA POR FORMA DE PAGO ---
            temp_df = df_filtrado.groupby('forma_pago')['monto'].sum().reset_index()
            st.plotly_chart(px.pie(temp_df, values='monto', names='forma_pago', title="Por Forma de Pago", hole=0.4), use_container_width=True)

        # --- TABLA ---
        st.markdown("---")
        df_display = df_filtrado.copy().sort_values(by='fecha', ascending=False)
        df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

st.sidebar.success("Conectado a Supabase")
