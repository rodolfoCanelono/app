# --- PESTAÑA 3: ANÁLISIS TEMPORAL ---
with tab3:
    # Usamos el DataFrame original 'df' cargado desde la DB
    if not df.empty:
        st.subheader("📅 Análisis de Evolución y Participación Real")
        
        # 1. CREACIÓN DE DF_TEMP (Definición de la variable)
        df_temp = df.copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        df_temp = df_temp.sort_values('fecha')
        df_temp['mes_año'] = df_temp['fecha'].dt.strftime('%Y-%m')
        
        # 2. AGRUPACIONES (Sumando 'monto')
        # Agrupación por mes y responsable para las barras
        resumen_mensual = df_temp.groupby(['mes_año', 'responsable'])['monto'].sum().reset_index()
        
        # Agrupación total histórica para la torta
        total_historico = df_temp.groupby('responsable')['monto'].sum().reset_index()

        # 3. GRÁFICO DE BARRAS APILADAS (Comparativa Mensual)
        st.write("**Distribución Mensual del Gasto ($)**")
        fig_barras = px.bar(
            resumen_mensual,
            x='mes_año',
            y='monto',
            color='responsable',
            barmode='stack',
            title="Suma de Gastos Mensuales por Responsable",
            text_auto='.2s',
            labels={'monto': 'Total Pagado ($)', 'mes_año': 'Mes'}
        )
        st.plotly_chart(fig_barras, use_container_width=True)

        st.markdown("---")

        # 4. GRÁFICOS DE TORTA (Participación)
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.write("**Proporción del Gasto Histórico Total**")
            fig_pie = px.pie(
                total_historico, 
                values='monto', # Crucial: usar monto para evitar el 33%
                names='responsable',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie.update_traces(textinfo='percent+value', texttemplate='%{percent}<br>$%{value:,.0f}')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_t2:
            st.write("**Resumen Numérico Mensual**")
            # Pivotar para la tabla
            pivot_mes = resumen_mensual.pivot(index='mes_año', columns='responsable', values='monto').fillna(0)
            pivot_mes['Total'] = pivot_mes.sum(axis=1)
            st.dataframe(pivot_mes.style.format("${:,.0f}"), use_container_width=True)
            
    else:
        st.info("No hay datos disponibles para el análisis. Por favor, registra un gasto primero.")
