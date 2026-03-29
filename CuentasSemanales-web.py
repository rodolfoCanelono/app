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

# --- LISTAS ---
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

# --- INTERFAZ ---
st.title("📊 Gestión de Gastos del Hogar")
tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard"])

with tab1:
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            concepto_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto", min_value=1000, step=1000, format="%d")
            forma_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with col2:
            fecha_in = st.date_input("Fecha", datetime.now())
            resp_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fecha_in, concepto_in, monto_in, resp_in, forma_in):
                st.success("✅ Registrado con éxito"); st.rerun()

with tab2:
    df = cargar_datos_db()
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        # Crear columna de Mes para el análisis
        df['mes_año'] = df['fecha'].dt.to_period('M').astype(str)

        # --- FILTROS ---
        st.subheader("🔍 Filtros")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: inicio = st.date_input("Desde", df['fecha'].min().date())
        with col_f2: fin = st.date_input("Hasta", df['fecha'].max().date())
        with col_f3: resp_filtro = st.selectbox("Filtrar por Responsable", ["Todos"] + LISTA_RESPONSABLES)

        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if resp_filtro != "Todos": mask = mask & (df['responsable'] == resp_filtro)
        df_f = df.loc[mask]

        # --- NUEVA VISTA: TOTALES POR MES Y PERSONA ---
        st.markdown("---")
        st.subheader("📅 Análisis Mensual y por Responsable")
        
        col_m1, col_m2 = st.columns([1, 2])
        
        with col_m1:
            st.write("**Resumen de Totales**")
            # Tabla resumen agrupada
            resumen_mes = df_f.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
            # Pivotar para mejor lectura: Filas (Mes), Columnas (Persona)
            tabla_pivot = resumen_mes.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            # Agregar columna de Total Mes
            tabla_pivot['Total Mes'] = tabla_pivot.sum(axis=1)
            st.dataframe(tabla_pivot.style.format("${:,.0f}"), use_container_width=True)

        with col_m2:
            # Gráfico de Barras Comparativo
            fig_mes = px.bar(
                resumen_mes, 
                x='mes_año', 
                y='monto', 
                color='responsable',
                barmode='group',
                title="Gasto Mensual por Responsable",
                labels={'mes_año': 'Mes', 'monto': 'Monto ($)', 'responsable': 'Quién Pagó'},
                text_auto='.2s'
            )
            st.plotly_chart(fig_mes, use_container_width=True)

        # --- GRÁFICOS PIE ---
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(px.pie(df_f, values='monto', names='concepto', title="Distribución por Concepto", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df_f, values='monto', names='responsable', title="Participación Total", hole=0.4), use_container_width=True)
        with c3:
            st.plotly_chart(px.pie(df_f, values='monto', names='forma_pago', title="Uso de Medios de Pago", hole=0.4), use_container_width=True)

        # --- TABLA DETALLADA ---
        st.markdown("---")
        st.write("📋 **Historial Detallado**")
        df_f['fecha_str'] = df_f['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_f[['fecha_str', 'concepto', 'monto', 'responsable', 'forma_pago']].sort_values('fecha_str', ascending=False), use_container_width=True)
    else:
        st.info("No hay datos.")
