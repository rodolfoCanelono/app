import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA (PRIMERA LÍNEA OBLIGATORIA)
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
    """Carga Responsables y Conceptos dinámicamente"""
    try:
        response = supabase.table(tabla).select(columna).execute()
        lista = [r[columna] for r in response.data]
        return lista if lista else respaldo
    except:
        return respaldo

def cargar_datos_db():
    """Carga los registros de gastos con limpieza numérica"""
    try:
        response = supabase.table("gastos_hogar").select("*").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # LIMPIEZA CRÍTICA: Asegurar que monto sea número para evitar el error del 33%
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(float)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo = {
        "fecha": fecha.strftime("%Y-%m-%d"), 
        "concepto": concepto,
        "monto": float(monto), 
        "responsable": responsable, 
        "forma_pago": forma_pago
    }
    try:
        supabase.table("gastos_hogar").insert(nuevo).execute()
        return True
    except:
        return False

# =========================================================
# 4. INICIALIZACIÓN DE DATOS DINÁMICOS
# =========================================================
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer", "Machulon"])
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
                st.success("✅ Gasto guardado correctamente"); st.rerun()

# --- PESTAÑA 2: DASHBOARD (FILTROS COMPLETOS) ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Visualización")
        f1, f2, f3, f4 = st.columns(4)
        with f1: ini = st.date_input("Desde", df['fecha'].min().date(), key="dash_ini")
        with f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="dash_fin")
        with f3: qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="dash_qui")
        with f4: con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="dash_con")

        # Aplicar filtros
        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if qui != "Todos": mask = mask & (df['responsable'] == qui)
        if con != "Todos": mask = mask & (df['concepto'] == con)
        df_f = df.loc[mask]

        # Resumen 50/50
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        c_i, c_r, c_t = st.columns(3)
        with c_i: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with c_r: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with c_t: st.metric("Total Seleccionado", f"${total_f:,.0f}")

        # Gráficas
        g1, g2 = st.columns(2)
        with g1:
            df_g1 = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_g1, values='monto', names='concepto', hole=0.4, title="Gasto por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_g2 = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_g2, values='monto', names='responsable', hole=0.4, title="Gasto por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Detalle de Registros Filtrados")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("No hay datos.")

# --- PESTAÑA 3: CUADRE - APORTES ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas y Aportes")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio Periodo", df['fecha'].min().date(), key="c_ini")
        with cf2: c_fin = st.date_input("Fin Periodo", df['fecha'].max().date(), key="c_fin")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)]
        
        # --- CÁLCULO DE APORTES REALES ---
        # Agrupamos por responsable sumando montos
        resumen_cuadre = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_periodo = resumen_cuadre['monto'].sum()
        cuota_50_50 = total_periodo / 2
        
        # Calcular Saldo (Diferencia)
        resumen_cuadre['Saldo'] = resumen_cuadre['monto'] - cuota_50_50
        
        st.write(f"### Total Periodo: ${total_periodo:,.0f} | Cuota Ideal: ${cuota_50_50:,.0f}")
        
        col_pie, col_tab = st.columns([2, 1])
        with col_pie:
            # GRÁFICA DE TORTA CORREGIDA: Usa values='monto' y pre-agregado
            fig_pie_cuadre = px.pie(resumen_cuadre, values='monto', names='responsable', 
                                    hole=0.5, title="Participación en el Gasto")
            fig_pie_cuadre.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_cuadre, use_container_width=True)
        
        with col_tab:
            st.write("**Resumen de Saldos**")
            st.table(resumen_cuadre.style.format({"monto": "${:,.0f}", "Saldo": "${:,.0f}"}))
        
        st.markdown("---")
        st.write("### 📑 Cuadre Mensual Histórico")
        df_aux = df.copy(); df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        pivot['Total'] = pivot.sum(axis=1)
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- PESTAÑA 4: PRONÓSTICO ---
with tab4:
    if not df.empty:
        st.subheader("🔮 Pronóstico Basado en Promedios Mensuales")
        df_p = df.copy(); df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        # Promedio de totales mensuales (Si marzo es 80M, el promedio será alto)
        gastos_por_mes = df_p.groupby('mes')['monto'].sum().reset_index()
        promedio_mensual = gastos_por_mes['monto'].mean()
        
        st.info(f"El gasto promedio mensual es: **${promedio_mensual:,.0f}**")
        
        ultima_f = df_p['fecha'].max()
        proyeccion = []
        for i in range(1, 4):
            mes_f = (ultima_f + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyeccion.append({'mes': mes_f, 'monto': promedio_mensual, 'Tipo': 'Pronóstico'})
        
        df_proy = pd.DataFrame(proyeccion)
        gastos_por_mes['Tipo'] = 'Histórico'
        df_plot = pd.concat([gastos_por_mes, df_proy])

        fig_proy = px.bar(df_plot, x='mes', y='monto', color='Tipo', text_auto='.2s', title="Flujo de Caja Real vs Proyectado")
        st.plotly_chart(fig_proy, use_container_width=True)

st.sidebar.success("✅ Supabase Conectado")
