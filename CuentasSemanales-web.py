import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
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
# 3. FUNCIONES DE CARGA Y LIMPIEZA
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
            # Limpieza de montos para asegurar que sean numéricos
            df_raw['monto'] = (
                df_raw['monto']
                .astype(str)
                .str.replace(',', '', regex=False)
            )
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0)
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
# 4. INICIALIZACIÓN DE DATOS
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
            mon_in = st.number_input("Monto", min_value=2000, step=2000, format="%d")
            pag_in = st.selectbox("Forma de Pago", LISTA_FORMAS_PAGO)
        with c2:
            fec_in = st.date_input("Fecha", datetime.now())
            res_in = st.selectbox("Responsable", LISTA_RESPONSABLES)
        if st.form_submit_button("Guardar Gasto"):
            if guardar_gasto_db(fec_in, con_in, mon_in, res_in, pag_in):
                st.success("✅ Gasto guardado correctamente")
                st.rerun()

# --- TAB 2: DASHBOARD ---
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
        df_f = df.loc[mask].copy()

        total_f = int(df_f['monto'].sum())
        mitad = total_f / 2
        
        ci, cr, ct = st.columns(3)
        with ci: st.info(f"**Irisysleyer (50%)**\n\n${mitad:,.0f}")
        with cr: st.success(f"**Rodolfo (50%)**\n\n${mitad:,.0f}")
        with ct: st.metric("Total Selección", f"${total_f:,.0f}")

        g1, g2 = st.columns(2)
        with g1:
            df_sum_c = df_f.groupby('concepto')['monto'].sum().reset_index()
            fig1 = px.pie(df_sum_c, values='monto', names='concepto', hole=0.4, title="Monto por Concepto")
            fig1.update_traces(texttemplate='$%{value:,.0f}<br>(%{percent})', textinfo='text+percent')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_sum_r = df_f.groupby('responsable')['monto'].sum().reset_index()
            fig2 = px.pie(df_sum_r, values='monto', names='responsable', hole=0.4, title="Monto por Responsable")
            fig2.update_traces(texttemplate='$%{value:,.0f}<br>(%{percent})', textinfo='text+percent')
            st.plotly_chart(fig2, use_container_width=True)
            
        st.subheader("📋 Detalle de Registros")
        st.dataframe(df_f.sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- TAB 3: CUADRE - APORTES ---
with tab3:
    if not df.empty:
        st.subheader("⚖️ Cuadre de Cuentas del Periodo")
        cf1, cf2 = st.columns(2)
        with cf1: c_ini = st.date_input("Inicio Cuadre", df['fecha'].min().date(), key="c1")
        with cf2: c_fin = st.date_input("Fin Cuadre", df['fecha'].max().date(), key="c2")
        
        df_c = df[(df['fecha'].dt.date >= c_ini) & (df['fecha'].dt.date <= c_fin)].copy()
        res_cuadre = df_c.groupby('responsable')['monto'].sum().reset_index()
        total_p = res_cuadre['monto'].sum()
        cuota = total_p / 2
        res_cuadre['Saldo'] = res_cuadre['monto'] - cuota
        
        st.write(f"### Total Período: ${total_p:,.0f} | Cuota Ideal: ${cuota:,.0f}")
        
        col_g, col_t = st.columns([2, 1])
        with col_g:
            fig_pie_cuadre = px.pie(res_cuadre, values='monto', names='responsable', hole=0.5, title="Participación")
            fig_pie_cuadre.update_traces(texttemplate='$%{value:,.0f}<br>(%{percent})', textinfo='text+percent')
            st.plotly_chart(fig_pie_cuadre, use_container_width=True)
        
        with col_t:
            st.table(res_cuadre.style.format({"monto": "${:,.0f}", "Saldo": "${:,.0f}"}))
        
        st.markdown("---")
        df_aux = df_c.copy()
        df_aux['mes'] = df_aux['fecha'].dt.strftime('%Y-%m')
        pivot = df_aux.groupby(['mes', 'responsable'])['monto'].sum().unstack().fillna(0)
        st.write("### 📑 Historial Mensual")
        st.dataframe(pivot.style.format("${:,.0f}"), use_container_width=True)
    else:
        st.info("Sin datos.")

# --- TAB 4: PRONÓSTICO (REGRESIÓN LINEAL) ---
with tab4:
    if not df.empty:
        st.subheader("🔮 Pronóstico de Gastos (Regresión Lineal Simple)")
        
        # 1. Preparar datos históricos mensuales
        df_p = df.copy()
        df_p['mes_dt'] = df_p['fecha'].dt.to_period('M').dt.to_timestamp()
        gastos_mes = df_p.groupby('mes_dt')['monto'].sum().reset_index()
        gastos_mes = gastos_mes.sort_values('mes_dt')
        
        if len(gastos_mes) < 2:
            st.warning("Se requieren al menos 2 meses de datos históricos para realizar una regresión lineal.")
        else:
            # 2. Realizar Regresión Lineal Simple
            # X = índice numérico del mes (0, 1, 2...)
            # Y = monto gastado
            x = np.arange(len(gastos_mes))
            y = gastos_mes['monto'].values
            
            # Cálculo de coeficientes: y = mx + b
            m, b = np.polyfit(x, y, 1)
            
            # 3. Proyectar los siguientes 3 meses
            x_future = np.arange(len(gastos_mes), len(gastos_mes) + 3)
            y_future = m * x_future + b
            
            # Generar etiquetas de fechas futuras
            last_date = gastos_mes['mes_dt'].max()
            future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 4)]
            
            # 4. Crear DataFrame para visualización
            df_hist = pd.DataFrame({
                'Mes': gastos_mes['mes_dt'].dt.strftime('%Y-%m'),
                'Monto': y.astype(int),
                'Tipo': 'Histórico'
            })
            
            df_proy = pd.DataFrame({
                'Mes': [d.strftime('%Y-%m') for d in future_dates],
                'Monto': y_future.clip(min=0).astype(int), # Evitamos montos negativos
                'Tipo': 'Pronóstico'
            })
            
            df_plot = pd.concat([df_hist, df_proy], ignore_index=True)
            
            # 5. Mostrar información y gráfico
            tendencia = "ascendente 📈" if m > 0 else "descendente 📉"
            st.info(f"La tendencia de tus gastos es **{tendencia}**. Monto estimado para el próximo mes: **${int(y_future[0]):,.0f}**")
            
            fig_proy = px.bar(
                df_plot,
                x='Mes',
                y='Monto',
                color='Tipo',
                text='Monto',
                title="Proyección de Gastos para los Próximos 3 Meses",
                color_discrete_map={'Histórico': '#1f77b4', 'Pronóstico': '#ff7f0e'}
            )
            fig_proy.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_proy, use_container_width=True)
            
            # Fórmula matemática para contexto (LaTeX)
            st.write("### Modelo de Regresión")
            st.latex(fr"y = {m:.2f}x + {b:.2f}")
            st.caption("Donde 'x' es el índice del mes y 'y' es el gasto proyectado.")

    else:
        st.info("No hay datos suficientes para proyectar.")

st.sidebar.success("✅ Sistema Consolidado")
