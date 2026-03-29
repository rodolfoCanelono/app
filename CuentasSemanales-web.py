import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", page_icon=img_icono, layout="wide")
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# --- CONEXIÓN SUPABASE ---
url: str = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- LISTAS ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito"]
LISTA_CONCEPTOS = ["Comida", "Universidad Max", "Medicinas", "Ropa Max", "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", "SII - Box Bodega", "SII - Depto"]

def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable, forma_pago").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo_gasto = {"fecha": fecha.strftime("%Y-%m-%d"), "concepto": concepto, "monto": monto, "responsable": responsable, "forma_pago": forma_pago}
    try:
        supabase.table("gastos_hogar").insert(nuevo_gasto).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}"); return False

# --- INTERFAZ PRINCIPAL ---
st.title("📊 Gestión de Gastos del Hogar")
st.markdown("---")

# Se añade la tercera pestaña solicitada
tab1, tab2, tab3 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard Original", "📅 Análisis Temporal"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto", min_value=1000, step=1000, format="%d")
            forma_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col2:
            fecha_in = st.date_input("Fecha", datetime.now())
            resp_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, resp_in, forma_in):
                st.success("✅ Gasto registrado correctamente")
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    df = cargar_datos_db()
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Filtros Rápidos
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: inicio = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with col_f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with col_f3: quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_resp")

        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos": mask = mask & (df['responsable'] == quien)
        df_f = df.loc[mask]

        # Métricas Originales
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **División de Gastos (Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total General", f"${total_f:,.0f}")

        # Gráficos Originales
        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(px.pie(df_f, values='monto', names='concepto', title="Distribución por Concepto", hole=0.4), use_container_width=True)
        with col_g2:
            st.plotly_chart(px.pie(df_f, values='monto', names='responsable', title="Distribución por Responsable", hole=0.4), use_container_width=True)

        # Tabla de Historial
        st.markdown("---")
        df_historial = df_f.copy().sort_values('fecha', ascending=False)
        df_historial['fecha'] = df_historial['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_historial, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

# --- PESTAÑA 3: ANÁLISIS TEMPORAL ---
with tab3:
    if not df.empty:
        st.subheader("📅 Evolución Mensual de Gastos")
        
        # Preparación de datos temporales
        df['mes_año'] = df['fecha'].dt.to_period('M').astype(str)
        
        # Agrupamos por mes y responsable
        resumen_temporal = df.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
        
        # 1. GRÁFICO DE BARRAS APILADAS (Mejor para comparar y ver totales)
        fig_barra = px.bar(
            resumen_temporal, 
            x='mes_año', 
            y='monto', 
            color='responsable',
            title="Distribución Mensual por Quien Paga",
            labels={'mes_año': 'Periodo (Mes)', 'monto': 'Total ($)', 'responsable': 'Responsable'},
            text_auto='.2s', # Muestra el valor dentro de la barra
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_barra.update_layout(xaxis_type='category') # Asegura que los meses se vean en orden
        st.plotly_chart(fig_barra, use_container_width=True)

        st.markdown("---")
        
        # 2. GRÁFICO DE ÁREA PARA TENDENCIA (Más ilustrativo que línea simple)
        st.subheader("📈 Tendencia de Volumen de Gasto")
        tendencia_total = df.groupby('mes_año')['monto'].sum().reset_index()
        
        fig_area = px.area(
            tendencia_total,
            x='mes_año', 
            y='monto', 
            title="Fluctuación del Gasto Total Mensual",
            labels={'mes_año': 'Mes', 'monto': 'Gasto Total ($)'},
            markers=True,
            line_shape="spline" # Hace que la línea sea curva y suave
        )
        fig_area.update_traces(fillcolor="rgba(26, 115, 232, 0.2)", line_color="#1A73E8")
        st.plotly_chart(fig_area, use_container_width=True)

        # 3. TABLA DE DETALLE (Pivot)
        st.markdown("---")
        st.write("**Resumen Numérico Mensual**")
        pivot_mes = resumen_temporal.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
        pivot_mes['Total Mensual'] = pivot_mes.sum(axis=1)
        st.dataframe(pivot_mes.style.format("${:,.0f}"), use_container_width=True)
        
    else:
        st.info("Registra datos para ver el análisis temporal.")
st.sidebar.success("Conectado a Supabase")
