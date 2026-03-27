import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from sqlalchemy import create_engine, text

# 1. Configuración de la aplicación
st.set_page_config(
    page_title="Gestor de Gastos ICCI - Postgres",
    page_icon="💰",
    layout="wide" 
)

# --- CONFIGURACIÓN DEL MOTOR (ENGINE) ---
# Usamos directamente tu cadena de conexión de Supabase
DB_URL = "postgresql://postgres:Maniclo-2026@db.oldbexdvxquhbtpchqwe.supabase.co:5432/postgres"
engine = create_engine(DB_URL)

# --- LISTAS DE SELECCIÓN ESTÁNDAR ---
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

def inicializar_db():
    """Crea la tabla en Supabase si no existe"""
    try:
        with engine.connect() as conn:
            query = text("""
                CREATE TABLE IF NOT EXISTS gastos_hogar (
                    id SERIAL PRIMARY KEY,
                    fecha DATE NOT NULL,
                    concepto TEXT NOT NULL,
                    monto FLOAT NOT NULL,
                    responsable TEXT NOT NULL
                );
            """)
            conn.execute(query)
            conn.commit()
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")

def cargar_datos_db():
    """Consulta todos los datos usando el engine"""
    try:
        query = "SELECT fecha, concepto, monto, responsable FROM gastos_hogar;"
        # Leemos directamente a un DataFrame de Pandas
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(columns=['fecha', 'concepto', 'monto', 'responsable'])

def guardar_gasto_db(fecha, concepto, monto, responsable):
    """Inserta un nuevo registro usando el engine"""
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) 
                VALUES (:f, :c, :m, :r);
            """)
            conn.execute(
                query, 
                {"f": fecha, "c": concepto, "m": monto, "r": responsable}
            )
            conn.commit()
    except Exception as e:
        st.error(f"Error al guardar el gasto: {e}")

# Ejecutar inicialización
inicializar_db()

st.title("📊 Gastos del Hogar (PostgreSQL - Supabase)")
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
        st.success(f"✅ Registrado con éxito en Supabase.")
        st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos_db()

    if not df.empty:
        # Asegurar formato de fecha
        df['fecha'] = pd.to_datetime(df['fecha'])

        st.subheader("🔍 Filtros de Búsqueda")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            inicio = st.date_input("Desde", df['fecha'].min().date())
        with col_f2:
            fin = st.date_input("Hasta", df['fecha'].max().date())
        with col_f3:
            quien = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES)
        with col_f4:
            que_gasto = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS)

        # Aplicar filtros
        mask = (df['fecha'].dt.date >= inicio) & (df['fecha'].dt.date <= fin)
        if quien != "Todos":
            mask = mask & (df['responsable'] == quien)
        if que_gasto != "Todos":
            mask = mask & (df['concepto'] == que_gasto)
        
        df_filtrado = df.loc[mask]

        # --- SECCIÓN DE PAGOS ---
        st.markdown("---")
        total_filtrado = df_filtrado['monto'].sum()
        mitad = total_filtrado / 2
        
        st.write("⚖️ **División Equitativa**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Irisysleyer (50%)", f"${mitad:,.0f}")
        c2.metric("Rodolfo (50%)", f"${mitad:,.0f}")
        c3.metric("Total General", f"${total_filtrado:,.0f}")

        # --- GRÁFICAS ---
        st.markdown("---")
        c_graf1, c_graf2 = st.columns(2)
        
        with c_graf1:
            st.write("**Gasto por Concepto**")
            fig1 = px.pie(df_filtrado, values='monto', names='concepto', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)

        with c_graf2:
            st.write("**Gasto por Responsable**")
            fig2 = px.pie(df_filtrado, values='monto', names='responsable', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        # --- TABLA ---
        st.markdown("---")
        df_display = df_filtrado.copy().sort_values(by='fecha', ascending=False)
        df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, use_container_width=True)

    else:
        st.info("No hay datos para mostrar.")

st.sidebar.info(f"Conectado a: {DB_URL.split('@')[1]}")
