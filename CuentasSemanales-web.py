import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de la aplicación
st.set_page_config(
    page_title="Gestor de Gastos ICCI",
    page_icon="💰",
    layout="centered"
)

# Ruta del archivo Excel
NOMBRE_ARCHIVO = 'Gestion_Financiera.xlsx'

# Función para cargar los datos del Excel
def cargar_datos():
    if os.path.exists(NOMBRE_ARCHIVO):
        try:
            return pd.read_excel(NOMBRE_ARCHIVO)
        except Exception:
            return pd.DataFrame(columns=['Fecha', 'Concepto', 'Monto'])
    return pd.DataFrame(columns=['Fecha', 'Concepto', 'Monto'])

# --- LÓGICA DE INTERFAZ ---

st.title("📊 Mis Gastos del Hogar")
st.markdown("---")

# Crear dos pestañas: una para Cargar y otra para Ver Historial
tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard e Historial"])

with tab1:
    st.subheader("Nuevo Registro")
    
    # Formulario de entrada
    with st.form("form_gastos", clear_on_submit=True):
        concepto = st.text_input("¿En qué gastaste?", placeholder="Ej: Comidas, medicinas...")
        monto = st.number_input("Monto ($)", min_value=0.0, step=0.01, format="%.2f")
        fecha = st.date_input("Fecha del gasto", datetime.now(),format="DD/MM/YYYY")
        btn_guardar = st.form_submit_button("Guardar en Excel")

    if btn_guardar:
        if concepto and monto > 0:
            df_actual = cargar_datos()
            # Crear nueva fila
            nueva_fila = pd.DataFrame([{
                'Fecha': fecha.strftime("%Y-%m-%d"),
                'Concepto': concepto,
                'Monto': monto
            }])
            
            # Unir y guardar (Mantiene el orden de captura)
            df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
            df_final.to_excel(NOMBRE_ARCHIVO, index=False)
            
            st.success(f"✅ Registrado: {concepto} por ${monto:,.2f}")
            st.balloons() # Pequeña animación de éxito
        else:
            st.error("Por favor, ingresa un concepto y un monto válido.")

with tab2:
    st.subheader("Resumen de Gastos")
    df = cargar_datos()

    if not df.empty:
        # Métricas resaltadas
        total_gastado = df['Monto'].sum()
        num_registros = len(df)
        
        col1, col2 = st.columns(2)
        col1.metric("Gasto Total", f"${total_gastado:,.2f}")
        col2.metric("N° de Gastos", num_registros)

        st.markdown("---")
        
        # Filtro de búsqueda por texto
        busqueda = st.text_input("🔍 Buscar en el historial (Concepto)")
        
        if busqueda:
            df_vista = df[df['Concepto'].str.contains(busqueda, case=False, na=False)]
        else:
            df_vista = df

        # Mostrar tabla (el orden es el de captura, de arriba hacia abajo)
        st.dataframe(df_vista, use_container_width=True)

        # Opción para descargar el archivo directamente al celular
        with open(NOMBRE_ARCHIVO, "rb") as f:
            st.download_button(
                label="📥 Descargar Excel",
                data=f,
                file_name="Cuentas_Semanales.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No hay datos registrados todavía. Comienza en la pestaña de Registro.")

# Pie de página técnico
st.sidebar.markdown("### Configuración")
st.sidebar.info("Esta Web App guarda los datos en un archivo Excel local o en la nube según donde se despliegue.")
