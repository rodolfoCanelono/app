import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
    st.error("❌ Faltan credenciales de Supabase en los Secrets.")
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
            # Aseguramos tipado numérico para evitar el error del 33%
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
st.title("📊 Gestión Financiera Pro - Rodolfo Canelón")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📝 Registro", "📈 Dashboard", "⚖️ Cuadre - Aportes", "🔮 Pronóstico"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro")
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
                st.success("✅ Gasto guardado"); st.rerun()

# --- PESTAÑA 2: DASHBOARD (FILTROS COMPLETOS) ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros Dinámicos")
        f1, f2, f3, f4 = st.columns(4)
        with f1: ini = st.date_input("Desde", df['fecha'].min().date(), key="dash_ini")
        with f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="dash_fin")
        with f3: qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="dash_qui")
        with f4: con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="dash_con")

        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if qui != "Todos": mask = mask & (df['responsable'] == qui)
        if con != "Todos": mask = mask & (df['concepto'] == con)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total Seleccionado", f"${total_f:,.0f}")

        g1, g2 = st.columns(2)
        with g1:
            df_p_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig_c = px.pie(df_p_c, values='monto', names='concepto', hole=0.4, title="Gasto por Concepto")
            fig_c.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_c, use_container_width=True)
        with g2:
            df_p_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig_r = px.pie(df_p_r, values='monto', names='responsable', hole=0.4, title="Gasto por Responsable")
            fig_r.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_r, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Detalle de Registros Filtrados")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- PESTAÑA 3: CUADRE - APORTES (NUEVA GRÁFICA DE TORTA) ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio Cuadre", df['fecha'].min().date(), key="c_ini")
        with cf2: c_fin = st.date_input("Fin Cuadre", df['fecha'].max().date(), key="c_fin")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)]
        resumen = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_p = resumen['monto'].sum()
        cuota_ideal = total_p / 2
        resumen['Diferencia (Saldo)'] = resumen['monto'] - cuota_ideal
        
        st.write(f"### Resumen: ${total_p:,.0f} | Cuota Ideal 50/50: ${cuota_ideal:,.0f}")
        
        # --- NUEVA GRÁFICA DE TORTA PARA CUADRE ---
        col_g_c1, col_g_c2 = st.columns([2, 1])
        with col_g_c1:
            fig_pie_cuadre = px.pie(resumen, values='monto', names='responsable', 
                                    hole=0.5, title="Distribución de Aportes en el Periodo")
            fig_pie_cuadre.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_cuadre, use_container_width=True)
        
        with col_g_c2:
            st.write("**Resumen de Saldos**")
            st.table(resumen.style.format({"monto": "${:,.0f}", "Diferencia (Saldo)": "${:,.0f}"}))
        
        st.markdown("---")
        st.write("### 📑 Historial Mensual Pivotado")
        df_aux = df.copy(); df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        pivot['Total Mes'] = pivot.sum(axis=1)
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- PESTAÑA 4: PRONÓSTICO ---
with tab4:
    if not df.empty:
        st.subheader("🔮 Proyección de Gastos")
        df_p = df.copy(); df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        mensual = df_p.groupby('mes')['monto'].sum().reset_index()
        avg = mensual['monto'].mean()
        
        st.info(f"Promedio mensual real: **${avg:,.0f}**")
        
        futuro = pd.DataFrame({'mes': ["Mes +1", "Mes +2", "Mes +3"], 'monto': [avg]*3, 'Tipo': ['Pronóstico']*3})
        mensual['Tipo'] = 'Histórico'
        df_final = pd.concat([mensual, futuro])
        
        st.plotly_chart(px.bar(df_final, x='mes', y='monto', color='Tipo', text_auto='.2s', title="Flujo Proyectado"), use_container_width=True)

st.sidebar.success("✅ Conectado a Supabase")
