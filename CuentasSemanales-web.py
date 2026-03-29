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
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # --- CORRECCIÓN DE TIPADO CRÍTICA ---
            # Forzamos monto a float para que Plotly pueda sumar valores y no contar filas
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

# --- 5. CARGA DE DATOS GLOBAL ---
df = cargar_datos_db()

# --- 6. INTERFAZ DE USUARIO ---
st.title("📊 Sistema de Gestión de Gastos e Inteligencia Financiera")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📈 Dashboard Original", "🔮 Análisis y Pronóstico"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_registro", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto del Gasto", min_value=0, step=1000, format="%d")
            forma_pago_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col_reg2:
            fecha_in = st.date_input("Fecha", datetime.now())
            responsable_in = st.selectbox("¿Quién pagó?", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in, forma_pago_in):
                st.success("✅ Gasto guardado.")
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    if not df.empty:
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1: inicio = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with c_f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with c_f3: quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_res")

        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos": mask = mask & (df['responsable'] == quien)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        st.write(f"### Total Filtrado: ${total_f:,.0f}")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            # Agrupación explícita para asegurar SUMA
            df_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_c, values='monto', names='concepto', hole=0.4, title="Gasto por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            df_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_r, values='monto', names='responsable', hole=0.4, title="Gasto por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos.")

# --- PESTAÑA 3: ANÁLISIS Y PRONÓSTICO ---
with tab3:
    if not df.empty:
        # 1. Preparación de datos
        df_temp = df.copy()
        df_temp = df_temp.sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')

        # --- TABLA DE TOTALES POR RESPONSABLE (Calculada matemáticamente) ---
        st.subheader("💰 Resumen Histórico por Pagador")
        total_historico = df_temp.groupby('responsable')['monto'].sum().reset_index()
        suma_total = total_historico['monto'].sum()
        total_historico['% Real'] = (total_historico['monto'] / suma_total) * 100
        
        st.table(total_historico.style.format({"monto": "${:,.0f}", "% Real": "{:.2f}%"}))

        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.write("**Proporción Real del Gasto (Torta)**")
            # --- FIX DEFINITIVO: Usamos 'monto' (la suma) para evitar el 33% ---
            fig_pie_h = px.pie(total_historico, values='monto', names='responsable', hole=0.5)
            fig_pie_h.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_h, use_container_width=True)

        with col_an2:
            st.write("**Detalle Mensual ($)**")
            res_mes = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
            pivot = res_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)

        st.markdown("---")
        
        # 2. PRONÓSTICO
        st.subheader("🔮 Pronóstico de Gastos")
        total_por_mes = df_temp.groupby('mes_año')['monto'].sum().reset_index()
        promedio_mensual = total_por_mes['monto'].mean()
        
        st.info(f"El gasto promedio mensual es de: **${promedio_mensual:,.0f}**")
        
        ultima_fecha = df_temp['fecha'].max()
        proyecciones = []
        for i in range(1, 4):
            mes_f = (ultima_fecha + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyecciones.append({'mes_año': mes_f, 'monto': promedio_mensual, 'Tipo': 'Pronóstico'})
        
        df_futuro = pd.DataFrame(proyecciones)
        total_por_mes['Tipo'] = 'Histórico'
        df_final = pd.concat([total_por_mes, df_futuro])

        fig_pron = px.bar(df_final, x='mes_año', y='monto', color='Tipo', title="Historial vs Proyección (3 Meses)", text_auto='.2s')
        st.plotly_chart(fig_pron, use_container_width=True)
    else:
        st.info("Sin datos suficientes.")

st.sidebar.success("✅ Conectado a Supabase")
