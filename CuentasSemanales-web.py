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
            # Tipado numérico estricto para asegurar cálculos reales (evita el 33% erróneo)
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
LISTA_RESPONSABLES = cargar_lista_db("responsables_gastos", "nombre", ["Rodolfo", "Irisysleyer", "Machulon"])
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

# --- PESTAÑA 2: DASHBOARD ---
with tab2:
    if not df.empty:
        st.subheader("🔍 Filtros de Búsqueda")
        f1, f2, f3, f4 = st.columns(4)
        with f1: ini = st.date_input("Desde", df['fecha'].min().date(), key="ini")
        with f2: fin = st.date_input("Hasta", df['fecha'].max().date(), key="fin")
        with f3: qui = st.selectbox("Responsable", ["Todos"] + LISTA_RESPONSABLES, key="qui")
        with f4: con = st.selectbox("Concepto", ["Todos"] + LISTA_CONCEPTOS, key="con")

        mask = (df['fecha'].dt.date >= ini) & (df['fecha'].dt.date <= fin)
        if qui != "Todos": mask = mask & (df['responsable'] == qui)
        if con != "Todos": mask = mask & (df['concepto'] == con)
        df_f = df.loc[mask]

        total_f = df_f['monto'].sum()
        mitad = total_f / 2
        
        st.write("⚖️ **Resumen de Cuentas Filtradas**")
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Seleccionado", f"${total_f:,.0f}")

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

        st.markdown("---")
        st.subheader("📋 Detalle de Registros Filtrados")
        df_ver = df_f.copy().sort_values('fecha', ascending=False)
        df_ver['fecha'] = df_ver['fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_ver, use_container_width=True)
    else:
        st.info("Sin datos registrados.")

# --- PESTAÑA 3: ANÁLISIS Y PRONÓSTICO (RESTAURADA TOTALMENTE) ---
with tab3:
    if not df.empty:
        df_temp = df.copy().sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')

        # 1. CUADRE MENSUAL POR RESPONSABLE (Funcionalidad Recuperada)
        st.subheader("📑 Cuadre Mensual de Gastos")
        res_mes_resp = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
        tabla_cuadre = res_mes_resp.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
        tabla_cuadre['Total Mensual'] = tabla_cuadre.sum(axis=1)
        st.dataframe(tabla_cuadre.style.format("${:,.0f}"), use_container_width=True)

        st.markdown("---")
        
        # 2. DISTRIBUCIÓN % HISTÓRICA (Funcionalidad Recuperada)
        st.subheader("💰 Participación Total en el Gasto")
        total_hist = df_temp.groupby('responsable')['monto'].sum().reset_index()
        suma_final = total_hist['monto'].sum()
        total_hist['% Participación'] = (total_hist['monto'] / suma_final) * 100
        
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            # Torta de participación REAL
            fig_pie_h = px.pie(total_hist, values='monto', names='responsable', hole=0.5, title="Distribución del Capital Aportado")
            fig_pie_h.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie_h, use_container_width=True)
        with col_pie2:
            st.write("**Resumen Numérico Acumulado**")
            st.table(total_hist.style.format({"monto": "${:,.0f}", "% Participación": "{:.2f}%"}))

        st.markdown("---")

        # 3. PRONÓSTICO (Funcionalidad Restaurada)
        st.subheader("🔮 Proyección Próximos 3 Meses")
        totales_mes_p = df_temp.groupby('mes_año')['monto'].sum().reset_index()
        promedio_p = totales_mes_p['monto'].mean()
        
        st.info(f"El gasto promedio mensual real (basado en totales) es de: **${promedio_p:,.0f}**")
        
        ultima_f = df_temp['fecha'].max()
        proyeccion_list = []
        for i in range(1, 4):
            mes_fut = (ultima_f + pd.DateOffset(months=i)).strftime('%Y-%m')
            proyeccion_list.append({'mes_año': mes_fut, 'monto': promedio_p, 'Tipo': 'Pronóstico'})
        
        df_p_plot = pd.DataFrame(proyeccion_list)
        totales_mes_p['Tipo'] = 'Histórico'
        df_final_p = pd.concat([totales_mes_p, df_p_plot])

        fig_p_bar = px.bar(df_final_p, x='mes_año', y='monto', color='Tipo', text_auto='.2s', 
                           title="Evolución y Pronóstico de Gasto Total",
                           color_discrete_map={'Histórico': '#1f77b4', 'Pronóstico': '#ff7f0e'})
        st.plotly_chart(fig_p_bar, use_container_width=True)
    else:
        st.info("Agregue datos para generar el análisis.")

st.sidebar.success(f"✅ Conectado. {len(LISTA_RESPONSABLES)} responsables cargados.")
