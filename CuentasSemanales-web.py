import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# --- 1. CONFIGURACIÓN DE PÁGINA ---
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", page_icon=img_icono, layout="wide")
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not url or not key:
    st.error("❌ Faltan credenciales de Supabase en los Secrets de Streamlit.")
    st.stop()

supabase = create_client(url, key)

# --- 3. LISTAS DE SELECCIÓN ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito","Transferencia"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

# --- 4. FUNCIONES DE BASE DE DATOS ---
def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable, forma_pago").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # CORRECCIÓN DE TIPADO CRÍTICA: Forzamos monto a numérico para que las gráficas sumen correctamente
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(float)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo_gasto = {
        "fecha": fecha.strftime("%Y-%m-%d"),
        "concepto": concepto,
        "monto": float(monto),
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
st.title("📊 Gestión de Gastos e Inteligencia Financiera")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📈 Dashboard l", "🔮 Análisis y Pronóstico"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro de Gasto")
    with st.form("form_registro", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto del Gasto", min_value=2000, step=2000, format="%d")
            forma_pago_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col_reg2:
            fecha_in = st.date_input("Fecha", datetime.now())
            responsable_in = st.selectbox("¿Quién realizó el pago?", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in, forma_pago_in):
                st.success("✅ Gasto guardado.")
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Visualización")
        c_f1, c_f2, c_f3, c_f4 = st.columns(4) # Añadida cuarta columna para Concepto
        with c_f1: inicio = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with c_f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with c_f3: quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_res")
        with c_f4: que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="d_con")

        # Lógica de Filtrado Multicapa
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos": mask = mask & (df['responsable'] == quien)
        if que_gasto != "Todos": mask = mask & (df['concepto'] == que_gasto)
        df_f = df.loc[mask]

        # --- DIVISIÓN DE GASTOS ---
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **División de Gastos (Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total Filtrado", f"${total_f:,.0f}")

        # Gráficos de Torta Corregidos (Suma de montos)
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            df_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_c, values='monto', names='concepto', hole=0.4, title="Distribución por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_r, values='monto', names='responsable', hole=0.4, title="Participación por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)

        st.write("📋 **Historial Detallado**")
        df_display = df_f.copy().sort_values('fecha', ascending=False)
        df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

# --- PESTAÑA 3: ANÁLISIS Y PRONÓSTICO ---
with tab3:
    if not df.empty:
        st.subheader("📅 Análisis de Participación y Proyecciones")
        
        df_temp = df.copy().sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')

        # --- TABLA DE TOTALES POR PAGADOR ---
        st.write("### 💰 Resumen de Totales por Responsable")
        total_historico = df_temp.groupby('responsable')['monto'].sum().reset_index()
        suma_total_general = total_historico['monto'].sum()
        total_historico['% Participación'] = (total_historico['monto'] / suma_total_general) * 100
        
        st.table(total_historico.style.format({"monto": "${:,.0f}", "% Participación": "{:.2f}%"}))

        st.markdown("---")
        col_an1, col_an2 = st.columns(2)
        
        with col_an1:
            st.write("**Proporción Real del Gasto Total (Torta)**")
            fig_pie_h = px.pie(total_historico, values='monto', names='responsable', hole=0.5)
            fig_pie_h.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_h, use_container_width=True)

        with col_an2:
            st.write("**Detalle Mensual por Responsable ($)**")
            res_mes = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
            pivot = res_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            pivot['Total Mes'] = pivot.sum(axis=1)
            st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)

        st.markdown("---")
        
        # --- PRONÓSTICO ---
        st.subheader("🔮 Pronóstico de Gastos")
        total_por_mes = df_temp.groupby('mes_año')['monto'].sum().reset_index()
        promedio_mensual = total_por_mes['monto'].mean()
        
        st.info(f"Gasto promedio mensual actual: **${promedio_mensual:,.0f}**")
        
        ultima_fecha = df_temp['fecha'].max()
        proyecciones = []
        for i in range(1, 4):
            mes_f = (ultima_fecha + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyecciones.append({'mes_año': mes_f, 'monto': promedio_mensual, 'Tipo': 'Pronóstico'})
        
        df_futuro = pd.DataFrame(proyecciones)
        total_por_mes['Tipo'] = 'Histórico'
        df_final = pd.concat([total_por_mes, df_futuro])

        fig_pron = px.bar(df_final, x='mes_año', y='monto', color='Tipo', 
                         title="Evolución Histórica vs Proyección a 3 meses", 
                         text_auto='.2s', color_discrete_map={'Histórico': '#1f77b4', 'Pronóstico': '#ff7f0e'})
        st.plotly_chart(fig_pron, use_container_width=True)
    else:
        st.info("Debe registrar datos para generar el análisis.")

st.sidebar.success("✅ Conectado a Supabase")
