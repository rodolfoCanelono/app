import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
from supabase import create_client, Client
from PIL import Image

# --- 1. CONFIGURACIÓN DE PÁGINA ---
try:
    img_icono = Image.open("Rodolfo-Final.png")
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", page_icon=img_icono, layout="wide")
except:
    st.set_page_config(page_title="Gestor de Gastos - Rodolfo Canelón", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not url or not key:
    st.error("❌ Faltan credenciales de Supabase en los Secrets.")
    st.stop()

supabase = create_client(url, key)

# --- 3. FUNCIONES DE CARGA DINÁMICA ---

def cargar_lista_db(tabla, columna, respaldo):
    try:
        response = supabase.table(tabla).select(columna).execute()
        lista = [r[columna] for r in response.data]
        return lista if lista else respaldo
    except:
        return respaldo

def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("fecha, concepto, monto, responsable, forma_pago").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # Tipado numérico estricto para asegurar cálculos reales
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(float)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def guardar_gasto_db(fecha, concepto, monto, responsable, forma_pago):
    nuevo = {
        "fecha": fecha.strftime("%Y-%m-%d"), "concepto": concepto,
        "monto": float(monto), "responsable": responsable, "forma_pago": forma_pago
    }
    try:
        supabase.table("gastos_hogar").insert(nuevo).execute()
        return True
    except:
        return False

# --- 4. INICIALIZACIÓN ---
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer"])
LISTA_CONCEPTOS = cargar_lista_db("conceptos_gastos", "concepto", ["Comida", "Hipotecario"])
LISTA_FORMAS_PAGO = ["Efectivo", "Débito", "Crédito", "Transferencia"]

df = cargar_datos_db()

# --- 5. INTERFAZ ---
st.title("📊 Sistema Integral de Gastos - Rodolfo Canelón")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📈 Dashboard", "🔮 Análisis y Pronóstico"])

# --- PESTAÑA 1: REGISTRO ---
with tab1:
    st.subheader("Ingresar Nuevo Gasto")
    with st.form("form_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            mon_in = st.number_input("Monto", min_value=0, step=1000, format="%d")
            pag_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with c2:
            fec_in = st.date_input("Fecha", datetime.now())
            res_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Registro"):
            if guardar_gasto_db(fec_in, con_in, mon_in, res_in, pag_in):
                st.success("✅ Gasto guardado exitosamente"); st.rerun()

# --- PESTAÑA 2: DASHBOARD (RESTAURADA) ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Búsqueda")
        f1, f2, f3, f4 = st.columns(4)
        with f1: ini = st.date_input("Desde", df['fecha'].min().date(), key="ini")
        with f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="fin")
        with f3: qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="qui")
        with f4: con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="con")

        # Aplicar filtros
        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if qui != "Todos": mask = mask & (df['responsable'] == qui)
        if con != "Todos": mask = mask & (df['concepto'] == con)
        df_f = df.loc[mask]

        # Métricas Dinámicas
        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **Resumen de Cuentas Filtradas**")
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Seleccionado", f"${total_f:,.0f}")

        # Gráficas
        g1, g2 = st.columns(2)
        with g1:
            df_g1 = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_g1, values='monto', names='concepto', hole=0.4, title="Distribución por Concepto")
            fig1.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_g2 = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_g2, values='monto', names='responsable', hole=0.4, title="Distribución por Responsable")
            fig2.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig2, use_container_width=True)

        # VISTA DE DATOS (FUNCIONALIDAD RESTAURADA)
        st.markdown("---")
        st.subheader("📋 Detalle de Registros Filtrados")
        df_ver = df_f.copy().sort_values('fecha', ascending=False)
        df_ver['fecha'] = df_ver['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_ver, use_container_width=True)
    else:
        st.info("Sin datos registrados.")

# --- PESTAÑA 3: ANÁLISIS Y PRONÓSTICO ---
with tab3:
    if not df.empty:
        df_temp = df.copy().sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')

        st.subheader("💰 Resumen Histórico Acumulado")
        total_hist = df_temp.groupby('responsable')['monto'].sum().reset_index()
        st.table(total_hist.style.format({"monto": "${:,.0f}"}))

        # Pronóstico
        st.markdown("---")
        st.subheader("🔮 Proyección Próximos Meses")
        totales_mes = df_temp.groupby('mes_año')['monto'].sum().reset_index()
        promedio = totales_mes['monto'].mean()
        
        st.info(f"El gasto promedio mensual es de: **${promedio:,.0f}**")
        
        ultima = df_temp['fecha'].max()
        proyeccion = []
        for i in range(1, 4):
            m_f = (ultima + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyeccion.append({'mes_año': m_f, 'monto': promedio, 'Tipo': 'Pronóstico'})
        
        df_p = pd.DataFrame(proyeccion)
        totales_mes['Tipo'] = 'Histórico'
        df_final = pd.concat([totales_mes, df_p])

        fig_p = px.bar(df_final, x='mes_año', y='monto', color='Tipo', text_auto='.2s', title="Flujo de Caja Real vs Proyectado")
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.info("Agregue datos para generar el análisis temporal.")

st.sidebar.success(f"✅ Conectado a Supabase")
