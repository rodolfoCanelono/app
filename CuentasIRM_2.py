import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA
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
# 3. FUNCIONES DE CARGA Y LIMPIEZA (AHORA COMO ENTERO)
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
            # --- CAMBIO A ENTERO ---
            # Convertimos a numérico, llenamos vacíos con 0 y forzamos tipo int
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(int)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except: return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    # Aseguramos que el monto viaje como entero
    nuevo = {"fecha": fecha.strftime("%Y-%m-%d"), "concepto": concepto, "monto": int(monto), 
             "responsable": responsable, "forma_pago": forma_pago}
    try:
        supabase.table("gastos_hogar").insert(nuevo).execute()
        return True
    except: return False

# =========================================================
# 4. INICIALIZACIÓN
# =========================================================
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer", "Machulon"])
LISTA_CONCEPTOS = cargar_lista_db("conceptos_gastos", "concepto", ["Comida", "Hipotecario"])
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito", "Transferencia"]

df = cargar_datos_db()

# =========================================================
# 5. INTERFAZ (TABS)
# =========================================================
st.title("📊 Gestión Financiera Pro - Rodolfo Canelón")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📝 Registro", "📈 Dashboard", "⚖️ Cuadre - Aportes", "🔮 Pronóstico"])

# --- TAB 1: REGISTRO ---
with tab1:
    with st.form("f_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            # Input configurado para enteros
            mon_in = st.number_input("Monto (Entero)", min_value=0, step=1, format="%d")
            pag_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with c2:
            fec_in = st.date_input("Fecha", datetime.now())
            res_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fec_in, con_in, mon_in, res_in, pag_in):
                st.success("✅ Gasto guardado correctamente"); st.rerun()

# --- TAB 2: DASHBOARD (FILTROS COMPLETOS) ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Visualización")
        f1, f2, f3, f4 = st.columns(4)
        with f1: d_ini = st.date_input("Desde", df['fecha'].min().date(), key="d1")
        with f2: d_fin = st.date_input("Hasta", df['fecha'].max().date(), key="d2")
        with f3: d_qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="d3")
        with f4: d_con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="d4")

        mask = (df['fecha'].dt.date >= d_ini) & (df['fecha'].dt.date <= d_fin)
        if d_qui != "Todos": mask = mask & (df['responsable'] == d_qui)
        if d_con != "Todos": mask = mask & (df['concepto'] == d_con)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Selección", f"${total_f:,.0f}")

        g1, g2 = st.columns(2)
        with g1:
            df_pie_c = df_f.groupby('concepto', as_index=False)['monto'].sum()
            fig_c = px.pie(df_pie_c, values='monto', names='concepto', hole=0.4, title="Monto por Concepto")
            fig_c.update_traces(textinfo='value+percent', texttemplate='$%{value:,.0f}<br>%{percent}')
            st.plotly_chart(fig_c, use_container_width=True)
        with g2:
            df_pie_r = df_f.groupby('responsable', as_index=False)['monto'].sum()
            fig_r = px.pie(df_pie_r, values='monto', names='responsable', hole=0.4, title="Monto por Responsable")
            fig_r.update_traces(textinfo='value+percent', texttemplate='$%{value:,.0f}<br>%{percent}')
            st.plotly_chart(fig_r, use_container_width=True)
            
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else: st.info("Sin datos.")

# --- TAB 3: CUADRE - APORTES (TORTA Y SALDOS) ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas del Periodo")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio Cuadre", df['fecha'].min().date(), key="c1")
        with cf2: c_fin = st.date_input("Fin Cuadre", df['fecha'].max().date(), key="c2")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)]
        resumen_cuadre = df_c.groupby('responsable', as_index=False)['monto'].sum()
        total_p = resumen_cuadre['monto'].sum()
        cuota = total_p / 2
        resumen_cuadre['Diferencia (Saldo)'] = resumen_cuadre['monto'] - cuota
        
        st.write(f"### Total Periodo: ${total_p:,.0f} | Cuota Ideal 50/50: ${cuota:,.0f}")
        
        cg1, cg2 = st.columns([2, 1])
        with cg1:
            fig_pie_cuadre = px.pie(resumen_cuadre, values='monto', names='responsable', 
                                    hole=0.5, title="Participación Real")
            fig_pie_cuadre.update_traces(textinfo='value+percent', texttemplate='$%{value:,.0f}<br>%{percent}')
            st.plotly_chart(fig_pie_cuadre, use_container_width=True)
        with cg2:
            st.write("**Saldos de Cuadre**")
            st.table(resumen_cuadre.style.format({"monto": "${:,.0f}", "Diferencia (Saldo)": "${:,.0f}"}))
            
        st.markdown("---")
        df_aux = df.copy(); df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        st.write("### 📑 Historial Mensual")
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else: st.info("Sin datos.")

# --- TAB 4: PRONÓSTICO ---
with tab4:
    if not df.empty:
        st.subheader("🔮 Pronóstico de Flujo")
        df_p = df.copy(); df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        gastos_mes = df_p.groupby('mes', as_index=False)['monto'].sum()
        avg = gastos_mes['monto'].mean()
        
        st.info(f"Promedio mensual: **${avg:,.0f}**")
        
        proy = pd.DataFrame({'mes': ["Mes +1", "Mes +2", "Mes +3"], 'monto': [int(avg)]*3, 'Tipo': ['Pronóstico']*3})
        gastos_mes['Tipo'] = 'Histórico'
        df_plot = pd.concat([gastos_mes, proy])
        
        fig_proy = px.bar(df_plot, x='mes', y='monto', color='Tipo', text_auto='.2s', title="Flujo Proyectado")
        st.plotly_chart(fig_proy, use_container_width=True)

st.sidebar.success("✅ Sistema Configurado como Enteros")
