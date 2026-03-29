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
            # CORRECCIÓN DE TIPADO: Forzamos monto a numérico para que las gráficas sumen correctamente
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
st.title("📊 Sistema Integral de Gestión de Gastos")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Registro de Gastos", "📈 Dashboard Original", "🔮 Análisis y Pronóstico"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro de Gasto")
    with st.form("form_registro", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto del Gasto", min_value=0, step=1000, format="%d")
            forma_pago_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col_reg2:
            fecha_in = st.date_input("Fecha", datetime.now())
            responsable_in = st.selectbox("¿Quién realizó el pago?", LISTA_RESPONSABLES)
        
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in, forma_pago_in):
                st.success("✅ Gasto guardado correctamente.")
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ORIGINAL ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Visualización")
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1: inicio = st.date_input("Desde", df['fecha'].min().date())
        with c_f2: fin = st.date_input("Hasta", df['fecha'].max().date())
        with c_f3: quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)

        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos": mask = mask & (df['responsable'] == quien)
        df_f = df.loc[mask]

        # Métricas de División
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **División Equitativa (Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total Filtrado", f"${total_f:,.0f}")

        # Gráficos de Torta Corregidos
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            # Agregamos los datos antes de graficar para asegurar SUMA y no CONTEO
            df_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_c, values='monto', names='concepto', hole=0.4, title="Gasto por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_r, values='monto', names='responsable', hole=0.4, title="Participación por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)

        st.write("📋 **Historial de Transacciones**")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

# --- PESTAÑA 3: ANÁLISIS Y PRONÓSTICO ---
with tab3:
    if not df.empty:
        st.subheader("📅 Análisis de Participación y Proyecciones")
        
        # 1. Preparación de datos
        df_temp = df.copy()
        df_temp['monto'] = pd.to_numeric(df_temp['monto'], errors='coerce').fillna(0).astype(float)
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        df_temp = df_temp.sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')

        # --- SECCIÓN NUEVA: TABLA DE TOTALES POR PAGADOR ---
        st.write("### 💰 Resumen de Totales por Responsable")
        # Agrupamos por responsable y sumamos
        total_historico = df_temp.groupby('responsable')['monto'].sum().reset_index()
        # Calculamos el porcentaje real para la tabla
        suma_total_general = total_historico['monto'].sum()
        total_historico['% Participación'] = (total_historico['monto'] / suma_total_general) * 100
        
        # Mostramos la tabla con formato de moneda y porcentaje
        st.table(total_historico.style.format({
            "monto": "${:,.0f}",
            "% Participación": "{:.2f}%"
        }))

        st.markdown("---")

        # 2. Gráficos de Participación (Corregido para evitar el 33%)
        col_an1, col_an2 = st.columns(2)
        
    with col_an1:
    st.write("**Proporción del Gasto Total (Torta)**")
    
    # Asegúrate de usar 'monto' como valor numérico
    fig_pie_h = px.pie(
        total_historico, 
        values='monto',        # <--- CAMBIO CLAVE: Usa el dinero real, no el %
        names='responsable', 
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    
    # Plotly calculará el % automáticamente basándose en los montos
    # %{percent} mostrará el % real
    # %{value} mostrará el monto en pesos/dólares
    fig_pie_h.update_traces(
        textinfo='percent+value', 
        texttemplate='%{percent}<br>$%{value:,.0f}' 
    )
    
    st.plotly_chart(fig_pie_h, use_container_width=True)

        with col_an2:
            st.write("**Detalle Mensual por Responsable**")
            res_mes = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
            pivot = res_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            pivot['Total Mes'] = pivot.sum(axis=1)
            st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)

        st.markdown("---")
        
        # 3. Lógica de Pronóstico
        st.subheader("🔮 Pronóstico de Gastos")
        total_por_mes = df_temp.groupby('mes_año')['monto'].sum().reset_index()
        promedio_mensual = total_por_mes['monto'].mean()
        
        st.info(f"El gasto promedio mensual actual es de: **${promedio_mensual:,.0f}**")
        
        # Generar proyecciones
        ultima_fecha = df_temp['fecha'].max()
        proyecciones = []
        for i in range(1, 4):
            mes_f = (ultima_fecha + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyecciones.append({'mes_año': mes_f, 'monto': promedio_mensual, 'Tipo': 'Pronóstico'})
        
        df_futuro = pd.DataFrame(proyecciones)
        total_por_mes['Tipo'] = 'Histórico'
        df_final = pd.concat([total_por_mes, df_futuro])

        fig_pron = px.bar(
            df_final, x='mes_año', y='monto', color='Tipo',
            title="Evolución Histórica vs Proyección a 3 meses",
            text_auto='.2s',
            color_discrete_map={'Histórico': '#1f77b4', 'Pronóstico': '#ff7f0e'}
        )
        st.plotly_chart(fig_pron, use_container_width=True)
    else:
        st.info("No hay datos suficientes para realizar el análisis.")

st.sidebar.success("✅ Conectado a Supabase")
