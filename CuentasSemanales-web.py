import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
# Debe ser el primer comando de Streamlit
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(
        page_title="Gestor de Gastos - Rodolfo Canelón",
        page_icon=img_icono,
        layout="wide"
    )
except Exception:
    st.set_page_config(
        page_title="Gestor de Gastos - Rodolfo Canelón",
        layout="wide"
    )

# --- 2. CONFIGURACIÓN DE CONEXIÓN (SUPABASE) ---
url: str = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not url or not key:
    st.error("❌ Faltan las credenciales de Supabase en los Secrets.")
    st.stop()

supabase: Client = create_client(url, key)

# --- 3. LISTAS DE SELECCIÓN ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

# --- 4. FUNCIONES DE BASE DE DATOS ---
def cargar_datos_db():
    try:
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
        "forma_pago": forma_pago
    }
    try:
        supabase.table("gastos_hogar").insert(nuevo_gasto).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- 5. LÓGICA DE DATOS GLOBAL ---
df = cargar_datos_db()

# --- 6. INTERFAZ DE USUARIO ---
st.title("📊 Gestión de Gastos del Hogar")
st.markdown("---")

# Definición de las 3 pestañas (Corrige el NameError de tab3)
tab1, tab2, tab3 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard Original", "📅 Análisis Temporal"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto", min_value=1000, step=1000, format="%d")
            forma_pago_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col_reg2:
            fecha_in = st.date_input("Fecha", datetime.now())
            responsable_in = st.selectbox("¿Quién pagó?", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in, forma_pago_in):
                st.success(f"✅ Registrado: {concepto_in}")
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        st.subheader("🔍 Filtros Rápidos")
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1: inicio = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with c_f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with c_f3: quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_res")

        # Filtrado
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos": mask = mask & (df['responsable'] == quien)
        df_f = df.loc[mask]

        # Métricas de división
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **División de Gastos (Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total General", f"${total_f:,.0f}")

        # Gráficas de torta corregidas (suman monto)
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            df_concepto = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_concepto, values='monto', names='concepto', hole=0.4, title="Por Concepto")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_resp = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_resp, values='monto', names='responsable', hole=0.4, title="Por Responsable")
            st.plotly_chart(fig2, use_container_width=True)
            
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- PESTAÑA 3: ANÁLISIS TEMPORAL ---
with tab3:
    if not df.empty:
        st.subheader("📅 Evolución Mensual")
        
        # Preparación de datos temporales
        df_temp = df.copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        df_temp = df_temp.sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')
        
        # Agrupaciones sumando monto
        res_mes = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
        total_hist = df_temp.groupby('responsable')['monto'].sum().reset_index()

        # Gráfico Barras Apiladas (Comparativa Mensual)
        st.write("**¿Quién paga cada mes? (Suma de montos)**")
        fig_bar = px.bar(res_mes, x='mes_año', y='monto', color='responsable', barmode='stack', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        col_an1, col_an2 = st.columns(2)
        
        with col_an1:
            st.write("**Participación Total Real (Torta)**")
            fig_pie_hist = px.pie(total_hist, values='monto', names='responsable', hole=0.5)
            fig_pie_hist.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_hist, use_container_width=True)

        with col_an2:
            st.write("**Resumen Mensual ($)**")
            pivot = res_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            pivot['Total'] = pivot.sum(axis=1)
            st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Registra datos para ver el análisis.")

st.sidebar.success("Conectado a Supabase")
