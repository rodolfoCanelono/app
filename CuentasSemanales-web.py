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
# 3. FUNCIONES DE CARGA Y LIMPIEZA (FORZADO A ENTEROS)
# =========================================================

def cargar_lista_db(tabla, columna, respaldo):
    try:
        response = supabase.table(tabla).select(columna).execute()
        lista = [r[columna] for r in response.data]
        return lista if lista else respaldo
    except:
        return respaldo

def cargar_datos_db():
    try:
        response = supabase.table("gastos_hogar").select("*").execute()
        df_raw = pd.DataFrame(response.data)
        if not df_raw.empty:
            # LIMPIEZA MATEMÁTICA: Forzamos monto a entero para evitar errores de interpretación
            df_raw['monto'] = (
                df_raw['monto']
                .astype(str)
                .str.replace(',', '', regex=False)   # 🔥 QUITA COMAS DE MILES
            )
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0)
            #df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0).astype(int)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
        return df_raw
    except:
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

# --- TAB 1: REGISTRO ---
with tab1:
    st.subheader("Nuevo Registro de Gasto")
    with st.form("f_reg", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            con_in = st.selectbox("Concepto", LISTA_CONCEPTOS)
            mon_in = st.number_input("Monto", min_value=0, step=1, format="%d")
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

        # Filtrado
        mask = (df['fecha'].dt.date >= d_ini) & (df['fecha'].dt.date <= d_fin)
        if d_qui != "Todos": mask = mask & (df['responsable'] == d_qui)
        if d_con != "Todos": mask = mask & (df['concepto'] == d_con)
        df_f = df.loc[mask]

        # Métricas 50/50
        total_f = int(df_f['monto'].sum())
        mitad = total_f / 2
        
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Selección", f"${total_f:,.0f}")

        # Gráficas con paso a LISTA para asegurar montos reales
        g1, g2 = st.columns(2)
        with g1:
            df_sum_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            tot = df_sum_c['monto'].sum()
            porcentajes = [f"{(v/tot)*100:.1f}%" for v in df_sum_c['monto']]
            textos = [f"${monto:,.0f} ({p})" for monto, p in zip(df_sum_c['monto'], porcentajes)]
            fig1 = px.pie(
                df_sum_c,
                values='monto',
                names='concepto',
                hole=0.4,
                title="Monto por Concepto"
            )
            fig1.update_traces(text=textos,textinfo='text')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_sum_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            tot = df_sum_r['monto'].sum()
            porcentajes = [f"{(v/tot)*100:.1f}%" for v in df_sum_r['monto']]
            textos = [f"${monto:,.0f} ({p})" for monto, p in zip(df_sum_r['monto'], porcentajes)]
            fig2 = px.pie(
                df_sum_r,
                values='monto',
                names='responsable',
                hole=0.4,
                title="Monto por Responsable"
            )
            fig2.update_traces(text=textos,textinfo='text')
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("📋 Detalle de Registros")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- TAB 3: CUADRE - APORTES (Saldos con % actualizado) ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas del Periodo")
        
        # Filtros de fechas
        cf1, cf2 = st.columns(2)
        with cf1:
            c_ini = st.date_input("Inicio Cuadre", df['fecha'].min().date(), key="c1")
        with cf2:
            c_fin = st.date_input("Fin Cuadre", df['fecha'].max().date(), key="c2")
        
        # Filtrar DataFrame según fechas
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)].copy()
        
        # Agrupar por responsable y calcular total del periodo
        res_cuadre = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_p = res_cuadre['monto'].sum()
        cuota = total_p / 2
        res_cuadre['Saldo'] = res_cuadre['monto'] - cuota
        
        # Calcular porcentaje sobre el total
        res_cuadre['Porcentaje'] = res_cuadre['monto'] / total_p * 100
        
        st.write(f"### Total Período Seleccionado: ${total_p:,.0f} | Cuota Ideal: ${cuota:,.0f}")
        
        col_g, col_t = st.columns([2, 1])
        with col_g:
            # Gráfica de torta con monto + %
            res_cuadre['texto'] = res_cuadre.apply(
                lambda row: f"${row['monto']:,.0f} ({row['Porcentaje']:.1f}%)", axis=1
            )
            fig_pie_cuadre = px.pie(
                res_cuadre,
                values='monto',
                names='responsable',
                hole=0.5,
                title="Distribución de Aportes"
            )
            fig_pie_cuadre.update_traces(text=res_cuadre['texto'], textinfo='text')
            st.plotly_chart(fig_pie_cuadre, use_container_width=True)
        
        with col_t:
            # Mostrar tabla con Responsable, Monto, Saldo, Porcentaje
            st.write("**Saldos Calculados**")
            st.table(
                res_cuadre[['responsable', 'monto', 'Saldo', 'Porcentaje']].rename(
                    columns={'responsable': 'Responsable', 'monto': 'Monto', 'Saldo': 'Saldo', 'Porcentaje': 'Porcentaje (%)'}
                ).style.format({"Monto": "${:,.0f}", "Saldo": "${:,.0f}", "Porcentaje (%)": "{:.1f}%"} )
            )
        
        st.markdown("---")
        st.write("### 📑 Historial Mensual")
        df_aux = df_c.copy()
        df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        pivot['Total'] = pivot.sum(axis=1)
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
        
    else:
        st.info("Sin datos.")

# --- TAB 4: PRONÓSTICO (TOTALES MENSUALES) ---
with tab4:
    if not df.empty:
        st.subheader("🔮 Pronóstico de Flujo")
        
        # Preparar datos históricos por mes
        df_p = df.copy()
        df_p['mes'] = df_p['fecha'].dt.strftime('%Y-%m')
        gastos_mes = df_p.groupby('mes')['monto'].sum().reset_index()
        gastos_mes['Tipo'] = 'Histórico'
        
        # Promedio mensual para pronóstico
        avg = int(gastos_mes['monto'].mean())
        st.info(f"Promedio mensual real: **${avg:,.0f}**")
        
        # Crear proyección de los próximos 3 meses
        proy = pd.DataFrame({
            'mes': ["Mes +1", "Mes +2", "Mes +3"],
            'monto': [avg]*3,
            'Tipo': ['Pronóstico']*3
        })
        
        # Unir histórico + pronóstico
        df_plot = pd.concat([gastos_mes, proy], ignore_index=True)
        
        # Calcular porcentaje sobre el total general
        total_general = df_plot['monto'].sum()
        df_plot['porcentaje'] = df_plot['monto'] / total_general * 100
        
        # Texto combinado monto + porcentaje
        df_plot['texto'] = df_plot.apply(
            lambda row: f"${row['monto']:,.0f} ({row['porcentaje']:.1f}%)", axis=1
        )
        
        # Crear gráfico de barras con texto formateado
        fig_proy = px.bar(
            df_plot,
            x='mes',
            y='monto',
            color='Tipo',
            text='texto',
            title="Flujo Proyectado"
        )
        fig_proy.update_traces(textposition='outside')  # muestra el texto fuera de la barra
        st.plotly_chart(fig_proy, use_container_width=True)
st.sidebar.success("✅ Sistema Consolidado")
