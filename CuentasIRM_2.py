import plotly.express as px
from sqlalchemy import create_engine, text

# 1. Configuración de la página
st.set_page_config(
    page_title="Gestor de Gastos ICCI - Supabase",
    page_icon="💰",
    layout="wide"
)

# 2. Configuración de la base de datos (Supabase)
# Usamos el puerto 6543 que es más estable para redes con restricciones
DB_URL = "postgresql://postgres:Maniclo-2026@db.oldbexdvxquhbtpchqwe.supabase.co:6543/postgres?sslmode=require"

# Creamos el motor de conexión con parámetros de estabilidad
engine = create_engine(
    DB_URL,
    connect_args={"connect_timeout": 10},
    pool_pre_ping=True
)

# 3. Listas de selección
LISTA_RESPONSABLES = ["Rodolfo", "Irisysleyer", "Machulon"]
LISTA_CONCEPTOS = [
    "Comida", "Universidad Max", "Medicinas", "Ropa Max", 
    "Regalos", "Enseres", "Gastos Comunes", "Hipotecario", 
    "SII - Box Bodega", "SII - Depto"
]

# 4. Funciones de Base de Datos
def inicializar_db():
    """Crea la tabla si no existe al iniciar la app"""
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
        st.error(f"Error de conexión a Supabase: {e}")

def cargar_datos_db():
    """Trae los datos desde Supabase a un DataFrame"""
    try:
        query = "SELECT fecha, concepto, monto, responsable FROM gastos_hogar;"
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame(columns=['fecha', 'concepto', 'monto', 'responsable'])

def guardar_gasto_db(fecha, concepto, monto, responsable):
    """Inserta un nuevo registro"""
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO gastos_hogar (fecha, concepto, monto, responsable) 
                VALUES (:f, :c, :m, :r);
            """)
            conn.execute(query, {"f": fecha, "c": concepto, "m": monto, "r": responsable})
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- EJECUCIÓN INICIAL ---
inicializar_db()

# 5. Interfaz de Usuario (UI)
st.title("📊 Control de Gastos del Hogar")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Registrar Gasto", "📈 Análisis y Dashboard"])

# --- PESTAÑA 1: FORMULARIO ---
with tab1:
    st.subheader("Nuevo Registro de Gasto")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            concepto_sel = st.selectbox("Concepto", LISTA_CONCEPTOS)
            monto_num = st.number_input("Monto ($)", min_value=0, step=1000)
        
        with col2:
            fecha_sel = st.date_input("Fecha", datetime.now())
            responsable_sel = st.selectbox("Responsable", LISTA_RESPONSABLES)
        
        btn_enviar = st.form_submit_button("Guardar en Supabase")
        
        if btn_enviar:
            if monto_num > 0:
                if guardar_gasto_db(fecha_sel, concepto_sel, monto_num, responsable_sel):
                    st.success(f"✅ Gasto de {responsable_sel} guardado correctamente.")
                    st.rerun()
            else:
                st.warning("Por favor ingresa un monto mayor a 0.")

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    df = cargar_datos_db()
    
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Métricas rápidas
        total = df['monto'].sum()
        mitad = total / 2
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"${total:,.0f}")
        c2.metric("Cuota Irisysleyer", f"${mitad:,.0f}")
        c3.metric("Cuota Rodolfo", f"${mitad:,.0f}")
        
        st.markdown("---")
        
        # Gráficas
        g1, g2 = st.columns(2)
        with g1:
            fig_conc = px.pie(df, values='monto', names='concepto', title="Gastos por Concepto", hole=0.4)
            st.plotly_chart(fig_conc, use_container_width=True)
        with g2:
            fig_resp = px.pie(df, values='monto', names='responsable', title="Gastos por Responsable", hole=0.4)
            st.plotly_chart(fig_resp, use_container_width=True)
            
        # Tabla detallada
        st.subheader("Historial de Movimientos")
        st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay datos registrados en Supabase.")

# Barra lateral informativa
st.sidebar.markdown("### 🛠 Estado de Sistemas")
st.sidebar.info("Base de Datos: Supabase (PostgreSQL)")
st.sidebar.write(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
