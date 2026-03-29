import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", page_icon=img_icono, layout="wide")
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# --- 2. CONEXIÓN SUPABASE ---
url: str = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not url or not key:
    st.error("❌ Faltan credenciales de Supabase.")
    st.stop()

supabase: Client = create_client(url, key)

# --- 3. LISTAS ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito"]
LISTA_CONCEPTOS = ["Comida", "Universidad Max", "Medicinas", "Ropa Max", "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", "SII - Box Bodega", "SII - Depto"]

# --- 4. FUNCIONES DE BASE DE DATOS ---
def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable, forma_pago").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # --- CORRECCIÓN CRÍTICA: Asegurar que monto sea numérico ---
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo = {"fecha": fecha.strftime("%Y-%m-%d"), "concepto": concepto, "monto": float(monto), "responsable": responsable, "forma_pago": forma_pago}
    try:
        supabase.table("gastos_hogar").insert(nuevo).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}"); return False

# --- 5. CARGA DE DATOS ---
df = cargar_datos_db()

# --- 6. INTERFAZ ---
st.title("📊 Gestión de Gastos del Hogar")
tab1, tab2, tab3 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard Original", "📅 Análisis Temporal"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            concepto_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto", min_value=0, step=1000, format="%d")
            forma_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col2:
            fecha_in = st.date_input("Fecha", datetime.now())
            resp_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, resp_in, forma_in):
                st.success("✅ Registrado"); st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros Rápidos")
        c1, c2, c3 = st.columns(3)
        with c1: ini = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with c2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with c3: res = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_res")

        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if res != "Todos": mask = mask & (df['responsable'] == res)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **División de Gastos (Total / 2)**")
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with ct: st.metric("Total General", f"${total_f:,.0f}")

        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            # Agrupar y sumar explícitamente
            df_pie_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_pie_c, values='monto', names='concepto', title="Gasto por Concepto", hole=0.4)
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            # Agrupar y sumar explícitamente
            df_pie_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_pie_r, values='monto', names='responsable', title="Participación por Responsable", hole=0.4)
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos.")

# --- PESTAÑA 3: ANÁLISIS TEMPORAL ---
with tab3:
    if not df.empty:
        st.subheader("📅 Análisis de Participación Histórica")
        
        df_temp = df.copy().sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')
        
        # Agrupaciones clave (SUMA de monto)
        res_mes = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
        total_hist = df_temp.groupby('responsable')['monto'].sum().reset_index()

        # 1. Gráfico de Barras Apiladas (Volumen de gasto mensual)
        st.write("**Evolución Mensual (Suma de montos)**")
        fig_bar = px.bar(res_mes, x='mes_año', y='monto', color='responsable', barmode='stack', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.write("**Proporción Real del Gasto Histórico**")
            # --- FIX: Usar total_hist que contiene la suma de montos ---
            fig_pie_h = px.pie(total_hist, values='monto', names='responsable', hole=0.5, title="Distribución de Dinero Aportado")
            fig_pie_h.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_h, use_container_width=True)

        with col_t2:
            st.write("**Tabla Resumen Mensual ($)**")
            pivot = res_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            pivot['Total'] = pivot.sum(axis=1)
            st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Registra datos para ver el análisis.")

st.sidebar.success("Conectado a Supabase")
