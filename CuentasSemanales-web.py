import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# 1. Configuración de la aplicación
st.set_page_config(
    page_title="Gestor de Gastos ICCI",
    page_icon="💰",
    layout="wide" 
)

NOMBRE_ARCHIVO = 'Gestion_Financiera.xlsx'

# --- LISTAS DE SELECCIÓN ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = ["Comida", "Universidad Max", "Medicinas", "Ropa Max", "Regalos", "Enseres", "Depto"]

def cargar_datos():
    if os.path.exists(NOMBRE_ARCHIVO):
        try:
            df = pd.read_excel(NOMBRE_ARCHIVO)
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            if 'Responsable' not in df.columns:
                df['Responsable'] = "No especificado"
            return df
        except Exception:
            return pd.DataFrame(columns=['Fecha', 'Concepto', 'Monto', 'Responsable'])
    return pd.DataFrame(columns=['Fecha', 'Concepto', 'Monto', 'Responsable'])

st.title("📊 Gastos del Hogar")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard e Historial"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("Monto ($)", min_value=0.0, step=100.0)
        with col_reg2:
            fecha_in = st.date_input("Fecha del gasto", datetime.now(), format="DD/MM/YYYY")
            responsable_in = st.selectbox("¿Quién realizó el gasto?", LISTA_RESPONSABLES)
        
        boton_guardar = st.form_submit_button("Guardar Gasto")

    if boton_guardar:
        if monto_in > 0:
            df_actual = cargar_datos()
            nuevo_gasto = pd.DataFrame({
                'Fecha': [pd.to_datetime(fecha_in)], 
                'Concepto': [concepto_in], 
                'Monto': [monto_in],
                'Responsable': [responsable_in]
            })
            df_final = pd.concat([df_actual, nuevo_gasto], ignore_index=True)
            df_final.to_excel(NOMBRE_ARCHIVO, index=False)
            st.success(f"✅ Registrado con éxito")
            st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos()

    if not df.empty:
        # --- SECCIÓN DE FILTROS ---
        st.subheader("🔍 Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            inicio = st.date_input("Desde", df['Fecha'].min().date(), format="DD/MM/YYYY")
        with col_f2:
            fin = st.date_input("Hasta", df['Fecha'].max().date(), format="DD/MM/YYYY")
        with col_f3:
            quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
        with col_f4:
            que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS)

        # Lógica de Filtrado
        mask = (df['Fecha'].dt.date >= inicio) & (df['Fecha'].dt.date <= fin)
        if quien != "Todos":
            mask = mask & (df['Responsable'] == quien)
        if que_gasto != "Todos":
            mask = mask & (df['Concepto'] == que_gasto)
        
        df_filtrado = df.loc[mask]

        # --- SECCIÓN DE PAGOS DIVIDIDOS ---
        st.markdown("---")
        total_filtrado = df_filtrado['Monto'].sum()
        mitad = total_filtrado / 2
        
        st.write("⚖️ **División de Gastos (Monto Total / 2)**")
        c_i, c_r, c_t = st.columns(3)
        with c_i:
            st.info(f"**Irisysleyer**\n\n${mitad:,.0f}")
        with c_r:
            st.success(f"**Rodolfo**\n\n${mitad:,.0f}")
        with c_t:
            st.metric("Total General", f"${total_filtrado:,.0f}")

        # --- SECCIÓN DE GRÁFICAS ---
        st.markdown("---")
        st.subheader("📊 Análisis de Distribución")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.write("**Distribución por Concepto**")
            gastos_concepto = df_filtrado.groupby('Concepto')['Monto'].sum().reset_index()
            fig_pie_concepto = px.pie(gastos_concepto, values='Monto', names='Concepto', 
                                     hole=0.4, 
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie_concepto.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_concepto, use_container_width=True)

        with col_graf2:
            st.write("**Distribución por Responsable**")
            gastos_persona = df_filtrado.groupby('Responsable')['Monto'].sum().reset_index()
            fig_pie_persona = px.pie(gastos_persona, values='Monto', names='Responsable', 
                                    hole=0.4, 
                                    color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie_persona.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_persona, use_container_width=True)

        # --- TABLA DE DATOS ---
        st.markdown("---")
        st.write("📋 **Historial Detallado**")
        df_display = df_filtrado.copy().sort_values(by='Fecha', ascending=False)
        df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_display, use_container_width=True)

        # Botón de descarga
        with open(NOMBRE_ARCHIVO, "rb") as f:
            st.download_button(
                label="📥 Descargar Excel",
                data=f,
                file_name="Gestion_Financiera.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No hay datos que coincidan con los filtros.")

# Pie de página técnico
st.sidebar.markdown("### Configuración")
st.sidebar.info("Esta Web App guarda los datos en un archivo Excel local o en la nube según donde se despliegue.")
