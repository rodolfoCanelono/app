import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from sqlalchemy import text  # <--- Agrega esta línea
from sqlalchemy import create_engine

# 1. Configuración de la aplicación
st.set_page_config(
    page_title="Gestor de Gastos ICCI - Postgres",
    page_icon="💰",
    layout="wide" 
)

engine = create_engine("postgresql://postgres:Maniclo-2026@db.oldbexdvxquhbtpchqwe.supabase.co:5432/postgres")
conn = st.connection(
    "postgresql", 
    type="sql", 
    #url="postgresql://postgres:admin@localhost:5432/GastosIRM"
    url="postgresql://postgres:Maniclo-2026@db.oldbexdvxquhbtpchqwe.supabase.co:5432/postgres"
)

# --- LISTAS DE SELECCIÓN ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

from sqlalchemy import text # Importante importar esto

def inicializar_db():
    try:
        with conn.session as session:
            query = text("""
                CREATE TABLE IF NOT EXISTS gastos_hogar (
                    id SERIAL PRIMARY KEY,
                    fecha DATE NOT NULL,
                    concepto TEXT NOT NULL,
                    monto FLOAT NOT NULL,
                    responsable TEXT NOT NULL
                );
            """)
            session.execute(query)
            session.commit()
    except Exception as e:
        # Esto imprimirá el error real en tu terminal de VS Code / CMD
        st.error(f"Error de conexión: {e}")
        print(f"DEBUG ERROR: {e}")

def cargar_datos_db():
    """Consulta todos los datos de la tabla"""
    # ttl=0 asegura que no use caché y siempre traiga datos frescos
    return conn.query("SELECT fecha, concepto, monto, responsable FROM gastos_hogar;", ttl=0)

def guardar_gasto_db(fecha, concepto, monto, responsable):
    """Inserta un nuevo registro en Postgres"""
    with conn.session as session:
        # También envolvemos el INSERT
        query = text("""
            INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) 
            VALUES (:f, :c, :m, :r);
        """)
        session.execute(
            query, 
            {"f": fecha, "c": concepto, "m": monto, "r": responsable}
        )
        session.commit()

# Ejecutar inicialización
inicializar_db()

st.title("📊 Gastos del Hogar (PostgreSQL)")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gastos", "📈 Dashboard"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
    with st.form("form_gastos", clear_on_submit=True):
        col_reg1, col_reg2 = st.columns(2)
    
        with col_reg1:
            concepto_in = st.selectbox("¿En qué gastaste?", LISTA_CONCEPTOS)
            monto_in = st.number_input("¿Monto del Gasto?", min_value=1000, step=1000)
   
        with col_reg2:
            fecha_in = st.date_input("¿Fecha del gasto?", datetime.now(), format="DD/MM/YYYY")
            responsable_in = st.selectbox("¿Quién realizó el gasto?", LISTA_RESPONSABLES)
        
        boton_guardar = st.form_submit_button("Guardar Gasto")

    if boton_guardar:
        guardar_gasto_db(fecha_in, concepto_in, monto_in, responsable_in)
        st.success(f"✅ Registrado en Postgres: {concepto_in}")
        st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos_db()

    if not df.empty:
        # Asegurar que la fecha sea datetime para filtros
        df['fecha'] = pd.to_datetime(df['fecha'])

        st.subheader("🔍 Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            inicio = st.date_input("Desde", df['fecha'].min().date(), format="DD/MM/YYYY")
        with col_f2:
            fin = st.date_input("Hasta", df['fecha'].max().date(), format="DD/MM/YYYY")
        with col_f3:
            quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
        with col_f4:
            que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS)

        # Lógica de Filtrado
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos":
            mask = mask & (df['responsable'] == quien)
        if que_gasto != "Todos":
            mask = mask & (df['concepto'] == que_gasto)
        
        df_filtrado = df.loc[mask]

        # --- SECCIÓN DE PAGOS DIVIDIDOS ---
        st.markdown("---")
        total_filtrado = df_filtrado['monto'].sum()
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
            gastos_concepto = df_filtrado.groupby('concepto')['monto'].sum().reset_index()
            fig_pie_concepto = px.pie(gastos_concepto, values='monto', names='concepto', 
                                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie_concepto.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_concepto, use_container_width=True)

        with col_graf2:
            st.write("**Distribución por Responsable**")
            gastos_persona = df_filtrado.groupby('responsable')['monto'].sum().reset_index()
            fig_pie_persona = px.pie(gastos_persona, values='monto', names='responsable', 
                                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            fig_pie_persona.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_persona, use_container_width=True)

        # --- TABLA DE DATOS ---
        st.markdown("---")
        st.write("📋 **Historial Detallado**")
        df_display = df_filtrado.copy().sort_values(by='fecha', ascending=False)
        df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)

    else:
        st.info("No hay datos que coincidan con los filtros.")

st.sidebar.markdown("### Configuración")
st.sidebar.success("Conectado a PostgreSQL")
