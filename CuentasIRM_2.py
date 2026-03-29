import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA (PRIMERA LÍNEA)
# =========================================================
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", page_icon=img_icono, layout="wide")
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# =========================================================
# 2. CONEXIÓN A SUPABASE
# =========================================================
url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not url or not key:
    st.error("❌ Faltan credenciales de Supabase.")
    st.stop()

supabase = create_client(url, key)

# =========================================================
# 3. FUNCIONES DE CARGA Y GUARDADO
# =========================================================

def cargar_lista_db(tabla, columna, respaldo):
    try:
        response = supabase.table(tabla).select(columna).execute()
        return [r[columna] for r in response.data] if response.data else respaldo
    except: return respaldo

def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("*").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(float)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except: return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo = {"fecha": fecha.strftime("%Y-%m-%d"), "concepto": concepto, "monto": float(monto), 
             "responsable": responsable, "forma_pago": forma_pago}
    try:
        supabase.table("gastos_hogar").insert(nuevo).execute()
        return True
    except: return False

# =========================================================
# 4. INICIALIZACIÓN
# =========================================================
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer"])
LISTA_CONCEPTOS = cargar_lista_db("conceptos_gastos", "concepto", ["Comida", "Hipotecario"])
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito", "Transferencia"]

df = cargar_datos_db()

# =========================================================
# 5. INTERFAZ PRINCIPAL
# =========================================================
st.title("📊 Gestión Financiera Inteligente - Rodolfo Canelón")
st.markdown("---")

t1, t2, t3, t4 = st.tabs(["📝 Registro", "📈 Dashboard", "⚖️ Cuadre - Aportes", "🔮 Pronóstico"])

# --- TAB 1: REGISTRO ---
with t1:
    with st.form("f_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            mon_in = st.number_input("Monto", min_value=0, step=1000)
            pag_in = st.selectbox("Pago", LISTA_FORMAS_PAGO)
        with c2:
            fec_in = st.date_input("Fecha", datetime.now())
            res_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar"):
            if guardar_gasto_db(fec_in, con_in, mon_in, res_in, pag_in):
                st.success("Registrado"); st.rerun()

# --- TAB 2: DASHBOARD ---
with t2:
    if not df.empty:
        colf1, colf2 = st.columns(2)
        with colf1: d_ini = st.date_input("Desde", df['fecha'].min(), key="d1")
        with colf2: d_fin = st.date_input("Hasta", df['fecha'].max(), key="d2")
        
        df_f = df[(df['fecha'].dt.date >= d_ini) & (df['fecha'].dt.date <= d_fin)]
        st.metric("Gasto Total Periodo", f"${df_f['monto'].sum():,.0f}")
        
        g1, g2 = st.columns(2)
        fig_c = px.pie(df_f.groupby('concepto')['monto'].sum().reset_index(), values='monto', names='concepto', title="Por Concepto")
        g1.plotly_chart(fig_c, use_container_width=True)
        fig_r = px.pie(df_f.groupby('responsable')['monto'].sum().reset_index(), values='monto', names='responsable', title="Por Responsable")
        g2.plotly_chart(fig_r, use_container_width=True)
        
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)

# --- TAB 3: CUADRE - APORTES (FILTRO INCORPORADO) ---
with t3:
    if not df.empty:
        st.subheader("🔍 Filtro de Cuadre Específico")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio del Cuadre", df['fecha'].min(), key="c1")
        with cf2: c_fin = st.date_input("Fin del Cuadre", df['fecha'].max(), key="c2")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)]
        
        # Cálculo de Aportes Reales
        resumen_aportes = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_periodo = resumen_aportes['monto'].sum()
        cuota_ideal = total_periodo / 2
        
        st.write(f"### Resumen del Periodo: ${total_periodo:,.0f}")
        st.write(f"Cada uno debería aportar: **${cuota_ideal:,.0f}**")
        
        # Tabla de Cuadre
        resumen_aportes['Diferencia (Saldo)'] = resumen_aportes['monto'] - cuota_ideal
        st.table(resumen_aportes.style.format({"monto": "${:,.0f}", "Diferencia (Saldo)": "${:,.0f}"}))
        
        # Gráfico de Cuadre Mensual Histórico
        df_c_aux = df.copy(); df_c_aux['mes'] = df_c_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_c_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        st.write("### 📑 Historial de Cuadres Mensuales")
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- TAB 4: PRONÓSTICO ---
with t4:
    if not df.empty:
        df_p = df.copy(); df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        mensual = df_p.groupby('mes')['monto'].sum().reset_index()
        avg = mensual['monto'].mean()
        
        st.info(f"Promedio de gasto mensual: **${avg:,.0f}**")
        
        futuro = pd.DataFrame({'mes': ["Proyección 1", "Proyección 2", "Proyección 3"], 
                               'monto': [avg]*3, 'Tipo': ['Pronóstico']*3})
        mensual['Tipo'] = 'Histórico'
        total_p = pd.concat([mensual, futuro])
        
        st.plotly_chart(px.bar(total_p, x='mes', y='monto', color='Tipo', title="Proyección de Flujo"), use_container_width=True)

st.sidebar.success("✅ Supabase Conectado")
