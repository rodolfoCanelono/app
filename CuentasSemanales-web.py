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
        st.subheader("📅 Análisis de Evolución Mensual")
        
        # 1. Preparación robusta de datos
        df_temp = df.copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        # Ordenamos por fecha primero para que el gráfico sea cronológico
        df_temp = df_temp.sort_values('fecha')
        # Creamos la etiqueta de mes (Ej: 2024-01)
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')
        
        # Agrupación para los gráficos
        resumen_mensual = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()

        # 2. GRÁFICO 1: COMPARATIVA DE BARRAS APILADAS
        # Este gráfico permite ver el total del mes y cuánto puso cada uno
        st.write("**¿Quién paga cada mes? (Distribución Acumulada)**")
        fig_barras = px.bar(
            resumen_mensual,
            x='mes_año',
            y='monto',
            color='responsable',
            title="Gasto Total Mensual por Responsable",
            labels={'mes_año': 'Mes', 'monto': 'Suma de Monto ($)', 'responsable': 'Quién Pagó'},
            text_auto='.2s', # Muestra el valor abreviado (ej: 1.2M)
            barmode='stack'   # Apila las barras una sobre otra
        )
        fig_barras.update_layout(xaxis_title="Mes", yaxis_title="Monto Total ($)")
        st.plotly_chart(fig_barras, use_container_width=True)

        st.markdown("---")

        # 3. GRÁFICO 2: TENDENCIA DE ÁREA (Más ilustrativo)
        # Ideal para ver si el gasto sube o baja en el tiempo
        st.write("**Tendencia y Volumen de Gasto**")
        fig_area = px.area(
            resumen_mensual,
            x='mes_año',
            y='monto',
            color='responsable',
            title="Evolución del Flujo de Caja por Responsable",
            labels={'mes_año': 'Mes', 'monto': 'Monto ($)'},
            line_shape="spline", # Curvas suaves
            markers=True
        )
        fig_area.update_layout(xaxis_title="Línea de Tiempo", yaxis_title="Volumen de Gasto ($)")
        st.plotly_chart(fig_area, use_container_width=True)

        # 4. TABLA RESUMEN (PIVOT)
        st.markdown("---")
        st.write("**Detalle Numérico Mensual**")
        tabla_pivot = resumen_mensual.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
        # Añadir fila de totales por persona (opcional)
        tabla_pivot.loc['TOTAL'] = tabla_pivot.sum()
        st.dataframe(tabla_pivot.style.format("${:,.0f}"), use_container_width=True)
        
    else:
        st.info("No hay datos suficientes para generar el análisis temporal. Por favor, registra algunos gastos primero.")
st.sidebar.success("Conectado a Supabase")
