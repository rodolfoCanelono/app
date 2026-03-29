import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LA PRIMERA LÍNEA)
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
    st.error("❌ Faltan credenciales de Supabase en los Secrets.")
    st.stop()

supabase = create_client(url, key)

# =========================================================
# 3. FUNCIONES DE CARGA DINÁMICA
# =========================================================

def cargar_lista_db(tabla, columna, respaldo):
    try:
        response = supabase.table(tabla).select(columna).execute()
        lista = [r[columna] for r in response.data]
        return lista if lista else respaldo
    except: return respaldo

def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("*").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # LIMPIEZA CRÍTICA: Convertir a número para que los gráficos sumen dinero
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
# 4. INICIALIZACIÓN DE DATOS
# =========================================================
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer", "Machulon"])
LISTA_CONCEPTOS = cargar_lista_db("conceptos_gastos", "concepto", ["Comida", "Hipotecario"])
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito", "Transferencia"]

df = cargar_datos_db()

# =========================================================
# 5. INTERFAZ PRINCIPAL (DEFINICIÓN DE TABS)
# =========================================================
st.title("📊 Gestión Financiera Pro - Rodolfo Canelón")
st.markdown("---")

# Se definen las 4 pestañas para evitar el NameError
tab1, tab2, tab3, tab4 = st.tabs(["📝 Registro", "📈 Dashboard", "⚖️ Cuadre - Aportes", "🔮 Pronóstico"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("f_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            mon_in = st.number_input("Monto", min_value=0, step=1000, format="%d")
            pag_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with c2:
            fec_in = st.date_input("Fecha", datetime.now())
            res_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fec_in, con_in, mon_in, res_in, pag_in):
                st.success("✅ Guardado"); st.rerun()

# --- TAB 2: DASHBOARD (FILTROS COMPLETOS) ---
with tab2:
    if not df.empty:
        f1, f2, f3, f4 = st.columns(4)
        with f1: ini = st.date_input("Desde", df['fecha'].min().date(), key="d_ini")
        with f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="d_fin")
        with f3: qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d_qui")
        with f4: con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="d_con")

        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if qui != "Todos": mask = mask & (df['responsable'] == qui)
        if con != "Todos": mask = mask & (df['concepto'] == con)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Seleccionado", f"${total_f:,.0f}")

        g1, g2 = st.columns(2)
        with g1:
            # SUMA REAL PARA LA TORTA
            df_p1 = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_p1, values='monto', names='concepto', hole=0.4, title="Por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_p2 = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_p2, values='monto', names='responsable', hole=0.4, title="Por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("📋 Detalle de Registros")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else: st.info("Sin datos.")

# --- TAB 3: CUADRE - APORTES (FILTROS Y SALDOS) ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas del Periodo")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio Cuadre", df['fecha'].min().date(), key="c1")
        with cf2: c_fin = st.date_input("Fin Cuadre", df['fecha'].max().date(), key="c2")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)]
        resumen_cuadre = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_p = resumen_cuadre['monto'].sum()
        cuota_ideal = total_p / 2
        resumen_cuadre['Saldo'] = resumen_cuadre['monto'] - cuota_ideal
        
        st.write(f"### Total Periodo: ${total_p:,.0f} | Cuota Ideal: ${cuota_ideal:,.0f}")
        
        c_pie, c_tab = st.columns([2, 1])
        with c_pie:
            # TORTA CORREGIDA (SUMA REAL)
            fig_pie_c = px.pie(resumen_cuadre, values='monto', names='responsable', hole=0.5, title="Participación en el Gasto")
            fig_pie_c.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_cuadre if 'fig_pie_cuadre' in locals() else fig_pie_c, use_container_width=True)
        with c_tab:
            st.write("**Saldos de Cuadre**")
            st.table(resumen_cuadre.style.format({"monto": "${:,.0f}", "Saldo": "${:,.0f}"}))
            
        st.write("### 📑 Tabla Mensual")
        df_aux = df.copy(); df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else: st.info("Sin datos.")

# --- TAB 4: PRONÓSTICO (TOTALES MENSUALES) ---
with tab4:
    if not df.empty:
        df_p = df.copy(); df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        gastos_mes = df_p.groupby('mes')['monto'].sum().reset_index()
        avg = gastos_mes['monto'].mean()
        
        st.info(f"Gasto promedio mensual: **${avg:,.0f}**")
        
        proy = pd.DataFrame({'mes': ["Mes +1", "Mes +2", "Mes +3"], 'monto': [avg]*3, 'Tipo': ['Pronóstico']*3})
        gastos_mes['Tipo'] = 'Histórico'
        df_plot = pd.concat([gastos_mes, proy])
        
        st.plotly_chart(px.bar(df_plot, x='mes', y='monto', color='Tipo', text_auto='.2s', title="Flujo Proyectado"), use_container_width=True)

st.sidebar.success("✅ Conectado a Supabase")
