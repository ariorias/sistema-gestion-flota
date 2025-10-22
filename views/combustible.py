# -*- coding: utf-8 -*-
# views/combustible.py - MÓDULO DE COMBUSTIBLE

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import date
from utils.helpers import get_db_connection

def modulo_combustible():
    """Módulo completo de control de combustible"""
    
    st.header("⛽ Control de Combustible y Rendimiento")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Registrar Carga", "📋 Historial", "📊 Análisis", "🚨 Anomalías"])
    
    # ==========================================
    # TAB 1: REGISTRAR CARGA
    # ==========================================
    with tab1:
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("""
                SELECT id, patente, marca, modelo, km_actual, tipo 
                FROM vehiculos 
                WHERE estado = 'activo' 
                ORDER BY patente
            """, conn)
            
            df_cond = pd.read_sql_query("""
                SELECT id, nombre, dni 
                FROM conductores 
                WHERE estado = 'activo' 
                ORDER BY nombre
            """, conn)
        finally:
            conn.close()
        
        if df_veh.empty:
            st.warning("⚠️ No hay vehículos activos")
            return
        
        vehiculos_dict = {f"{row['patente']} - {row['marca']} {row['modelo']}": 
                         (row['id'], row['km_actual'], row['tipo']) 
                         for _, row in df_veh.iterrows()}
        
        conductores_dict = {"(Sin especificar)": None}
        conductores_dict.update({f"{row['nombre']} (DNI: {row['dni']})": row['id'] 
                                for _, row in df_cond.iterrows()})
        
        with st.form("registro_combustible"):
            st.subheader("📝 Registrar Nueva Carga de Combustible")
            
            vehiculo_sel = st.selectbox("🚛 Vehículo", list(vehiculos_dict.keys()))
            veh_id, km_sugerido, tipo_veh = vehiculos_dict[vehiculo_sel]
            
            conductor_sel = st.selectbox("👨‍✈️ Conductor", list(conductores_dict.keys()))
            cond_id = conductores_dict[conductor_sel]
            
            col1, col2 = st.columns(2)
            fecha_carga = col1.date_input("📅 Fecha de Carga", value=date.today())
            km_carga = col2.number_input("🛣️ Kilometraje", value=km_sugerido, min_value=0)
            
            st.subheader("⛽ Detalles de la Carga")
            
            col1, col2, col3 = st.columns(3)
            
            # Tipo de combustible según vehículo
            tipo_combustible = col1.selectbox("Tipo de Combustible", [
                "diesel",
                "nafta",
                "gnc"
            ], index=0 if tipo_veh == "camion" else 1)
            
            litros = col2.number_input("Litros Cargados", min_value=0.1, step=5.0)
            costo_total = col3.number_input("Costo Total (ARS)", min_value=0.0, step=100.0)
            
            # Calcular precio por litro automáticamente
            precio_litro = round(costo_total / litros, 2) if litros > 0 else 0
            st.info(f"💰 Precio por litro: ${precio_litro:.2f}")
            
            estacion = st.text_input("🏪 Estación de Servicio", placeholder="Ej: YPF Ruta 9, Shell Centro, etc.")
            
            # Calcular rendimiento si hay carga previa
            conn = get_db_connection()
            try:
                ultima_carga = conn.execute("""
                    SELECT km, fecha FROM combustible 
                    WHERE vehiculo_id = ? 
                    ORDER BY fecha DESC, km DESC 
                    LIMIT 1
                """, (veh_id,)).fetchone()
                
                if ultima_carga and km_carga > ultima_carga['km']:
                    km_recorridos = km_carga - ultima_carga['km']
                    rendimiento_calc = round(km_recorridos / litros, 2)
                    
                    st.success(f"📊 **Rendimiento calculado:** {rendimiento_calc} km/litro")
                    st.caption(f"🛣️ Km recorridos desde última carga: {km_recorridos:,} km")
                else:
                    rendimiento_calc = None
                    st.info("ℹ️ Esta es la primera carga o el kilometraje no es mayor a la carga anterior")
            finally:
                conn.close()
            
            observaciones = st.text_area("📝 Observaciones", 
                                        placeholder="Ej: Tanque lleno, carga parcial, anomalía detectada, etc.")
            
            submitted = st.form_submit_button("💾 Guardar Carga", use_container_width=True)
            
            if submitted and litros > 0 and costo_total > 0:
                conn = get_db_connection()
                try:
                    # Actualizar kilometraje del vehículo
                    conn.execute("UPDATE vehiculos SET km_actual = ? WHERE id = ?", (km_carga, veh_id))
                    
                    # Insertar carga
                    conn.execute("""
                        INSERT INTO combustible 
                        (vehiculo_id, fecha, km, litros, costo_total, precio_litro, 
                         tipo_combustible, estacion, conductor_id, rendimiento, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (veh_id, fecha_carga, km_carga, litros, costo_total, precio_litro,
                         tipo_combustible, estacion, cond_id, rendimiento_calc, observaciones))
                    
                    conn.commit()
                    st.success("✅ Carga de combustible registrada exitosamente")
                    st.success(f"✅ Kilometraje actualizado a {km_carga:,} km")
                    
                    if rendimiento_calc:
                        # Alertar si el rendimiento es anormal
                        conn_check = get_db_connection()
                        try:
                            rend_prom = conn_check.execute("""
                                SELECT AVG(rendimiento) as prom 
                                FROM combustible 
                                WHERE vehiculo_id = ? AND rendimiento IS NOT NULL
                            """, (veh_id,)).fetchone()['prom']
                            
                            if rend_prom and rendimiento_calc < rend_prom * 0.7:
                                st.warning(f"⚠️ **ATENCIÓN:** Rendimiento 30% inferior al promedio ({rend_prom:.2f} km/l). Revisar vehículo.")
                        finally:
                            conn_check.close()
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
            elif submitted:
                st.warning("⚠️ Complete todos los campos obligatorios")
    
    # ==========================================
    # TAB 2: HISTORIAL
    # ==========================================
    with tab2:
        st.subheader("📋 Historial de Cargas")
        
        conn = get_db_connection()
        try:
            df_hist = pd.read_sql_query("""
                SELECT 
                    c.fecha,
                    v.patente,
                    c.km,
                    c.litros,
                    c.costo_total,
                    c.precio_litro,
                    c.rendimiento,
                    c.tipo_combustible,
                    c.estacion,
                    co.nombre as conductor
                FROM combustible c
                JOIN vehiculos v ON c.vehiculo_id = v.id
                LEFT JOIN conductores co ON c.conductor_id = co.id
                ORDER BY c.fecha DESC, c.km DESC
                LIMIT 200
            """, conn)
            
            if not df_hist.empty:
                # Filtros
                col1, col2, col3, col4 = st.columns(4)
                
                patentes = ["Todas"] + sorted(df_hist['patente'].unique().tolist())
                filtro_patente = col1.selectbox("Patente", patentes)
                
                tipos = ["Todos"] + sorted(df_hist['tipo_combustible'].unique().tolist())
                filtro_tipo = col2.selectbox("Combustible", tipos)
                
                fecha_desde = col3.date_input("Desde", value=date.today().replace(day=1))
                fecha_hasta = col4.date_input("Hasta", value=date.today())
                
                # Aplicar filtros
                df_filtrado = df_hist.copy()
                
                if filtro_patente != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['patente'] == filtro_patente]
                
                if filtro_tipo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['tipo_combustible'] == filtro_tipo]
                
                df_filtrado = df_filtrado[
                    (pd.to_datetime(df_filtrado['fecha']) >= pd.to_datetime(fecha_desde)) &
                    (pd.to_datetime(df_filtrado['fecha']) <= pd.to_datetime(fecha_hasta))
                ]
                
                # Estadísticas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 Total Cargas", len(df_filtrado))
                col2.metric("⛽ Total Litros", f"{df_filtrado['litros'].sum():,.0f} L")
                col3.metric("💰 Gasto Total", f"${df_filtrado['costo_total'].sum():,.2f}")
                col4.metric("📈 Rendimiento Prom.", 
                           f"{df_filtrado['rendimiento'].mean():.2f} km/l" 
                           if df_filtrado['rendimiento'].notna().any() else "N/A")
                
                # Tabla
                st.dataframe(
                    df_filtrado[['fecha', 'patente', 'km', 'litros', 'costo_total', 
                                'precio_litro', 'rendimiento', 'estacion', 'conductor']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "km": st.column_config.NumberColumn("KM", format="%d"),
                        "litros": st.column_config.NumberColumn("Litros", format="%.1f L"),
                        "costo_total": st.column_config.NumberColumn("Costo", format="$ %.2f"),
                        "precio_litro": st.column_config.NumberColumn("$/L", format="$ %.2f"),
                        "rendimiento": st.column_config.NumberColumn("Rend.", format="%.2f km/l")
                    }
                )
                
                # Exportar
                if st.button("📥 Exportar a Excel"):
                    st.info("🔄 Funcionalidad en desarrollo...")
                
            else:
                st.info("ℹ️ No hay cargas registradas")
        
        finally:
            conn.close()
    
    # ==========================================
    # TAB 3: ANÁLISIS
    # ==========================================
    with tab3:
        st.subheader("📊 Análisis de Consumo y Rendimiento")
        
        conn = get_db_connection()
        try:
            # Análisis por vehículo
            df_analisis = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    v.tipo,
                    COUNT(c.id) as total_cargas,
                    SUM(c.litros) as total_litros,
                    SUM(c.costo_total) as total_gastado,
                    AVG(c.rendimiento) as rendimiento_promedio,
                    MIN(c.rendimiento) as rendimiento_minimo,
                    MAX(c.rendimiento) as rendimiento_maximo,
                    AVG(c.precio_litro) as precio_promedio_litro
                FROM vehiculos v
                LEFT JOIN combustible c ON v.id = c.vehiculo_id
                WHERE v.estado = 'activo'
                GROUP BY v.id
                HAVING total_cargas > 0
                ORDER BY total_gastado DESC
            """, conn)
            
            if not df_analisis.empty:
                # Gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gasto por vehículo
                    fig_gasto = px.bar(
                        df_analisis.head(10),
                        x='patente',
                        y='total_gastado',
                        title='Top 10 - Gasto en Combustible',
                        labels={'total_gastado': 'Gasto Total (ARS)', 'patente': 'Patente'},
                        color='total_gastado',
                        color_continuous_scale='Reds'
                    )
                    fig_gasto.update_layout(height=400)
                    st.plotly_chart(fig_gasto, use_container_width=True)
                
                with col2:
                    # Rendimiento por vehículo
                    fig_rend = px.bar(
                        df_analisis.sort_values('rendimiento_promedio', ascending=False).head(10),
                        x='patente',
                        y='rendimiento_promedio',
                        title='Top 10 - Mejor Rendimiento',
                        labels={'rendimiento_promedio': 'Rendimiento (km/l)', 'patente': 'Patente'},
                        color='rendimiento_promedio',
                        color_continuous_scale='Greens'
                    )
                    fig_rend.update_layout(height=400)
                    st.plotly_chart(fig_rend, use_container_width=True)
                
                # Consumo por tipo de vehículo
                df_por_tipo = df_analisis.groupby('tipo').agg({
                    'total_litros': 'sum',
                    'total_gastado': 'sum',
                    'rendimiento_promedio': 'mean'
                }).reset_index()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_tipo_litros = px.pie(
                        df_por_tipo,
                        values='total_litros',
                        names='tipo',
                        title='Consumo por Tipo de Vehículo'
                    )
                    st.plotly_chart(fig_tipo_litros, use_container_width=True)
                
                with col2:
                    fig_tipo_gasto = px.pie(
                        df_por_tipo,
                        values='total_gastado',
                        names='tipo',
                        title='Gasto por Tipo de Vehículo'
                    )
                    st.plotly_chart(fig_tipo_gasto, use_container_width=True)
                
                # Tabla resumen
                st.subheader("📋 Resumen Detallado")
                st.dataframe(
                    df_analisis.round(2),
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.info("ℹ️ No hay suficientes datos para análisis")
        
        finally:
            conn.close()
    
    # ==========================================
    # TAB 4: ANOMALÍAS
    # ==========================================
    with tab4:
        st.subheader("🚨 Detección de Anomalías")
        
        conn = get_db_connection()
        try:
            anomalias = []
            
            # 1. Vehículos con bajo rendimiento
            df_bajo_rend = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    AVG(c.rendimiento) as rend_actual,
                    (SELECT AVG(rendimiento) FROM combustible WHERE rendimiento IS NOT NULL) as rend_general
                FROM vehiculos v
                JOIN combustible c ON v.id = c.vehiculo_id
                WHERE c.rendimiento IS NOT NULL
                GROUP BY v.id
                HAVING rend_actual < rend_general * 0.7
            """, conn)
            
            if not df_bajo_rend.empty:
                st.warning(f"⚠️ **{len(df_bajo_rend)} vehículos con rendimiento 30% inferior al promedio**")
                for _, row in df_bajo_rend.iterrows():
                    st.markdown(f"🔴 **{row['patente']}** - Rendimiento: {row['rend_actual']:.2f} km/l "
                              f"(Promedio flota: {row['rend_general']:.2f} km/l)")
                    st.caption("💡 Revisar: filtros de aire, inyectores, presión de neumáticos, estilo de conducción")
            
            # 2. Cargas sospechosas (alto consumo en poco tiempo)
            df_alto_consumo = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    c.fecha,
                    c.litros,
                    c.km,
                    LAG(c.km) OVER (PARTITION BY v.id ORDER BY c.fecha) as km_anterior,
                    LAG(c.fecha) OVER (PARTITION BY v.id ORDER BY c.fecha) as fecha_anterior
                FROM combustible c
                JOIN vehiculos v ON c.vehiculo_id = v.id
                ORDER BY c.fecha DESC
                LIMIT 50
            """, conn)
            
            if not df_alto_consumo.empty:
                df_alto_consumo['km_recorridos'] = df_alto_consumo['km'] - df_alto_consumo['km_anterior']
                df_alto_consumo['dias_transcurridos'] = (
                    pd.to_datetime(df_alto_consumo['fecha']) - 
                    pd.to_datetime(df_alto_consumo['fecha_anterior'])
                ).dt.days
                
                # Cargas muy frecuentes
                cargas_frecuentes = df_alto_consumo[
                    (df_alto_consumo['dias_transcurridos'] < 2) & 
                    (df_alto_consumo['litros'] > 50)
                ]
                
                if not cargas_frecuentes.empty:
                    st.warning(f"⚠️ **{len(cargas_frecuentes)} cargas sospechosamente frecuentes detectadas**")
                    for _, row in cargas_frecuentes.iterrows():
                        st.markdown(f"🟡 **{row['patente']}** - {row['litros']:.0f}L cargados en menos de 2 días")
            
            # 3. Variaciones extremas de rendimiento
            df_variacion = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    c.fecha,
                    c.rendimiento,
                    AVG(c.rendimiento) OVER (
                        PARTITION BY v.id 
                        ORDER BY c.fecha 
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) as rend_promedio_previo
                FROM combustible c
                JOIN vehiculos v ON c.vehiculo_id = v.id
                WHERE c.rendimiento IS NOT NULL
                ORDER BY c.fecha DESC
                LIMIT 100
            """, conn)
            
            if not df_variacion.empty:
                df_variacion['variacion_pct'] = (
                    (df_variacion['rendimiento'] - df_variacion['rend_promedio_previo']) / 
                    df_variacion['rend_promedio_previo'] * 100
                )
                
                variaciones_extremas = df_variacion[abs(df_variacion['variacion_pct']) > 30]
                
                if not variaciones_extremas.empty:
                    st.warning(f"⚠️ **{len(variaciones_extremas)} variaciones extremas de rendimiento**")
                    for _, row in variaciones_extremas.iterrows():
                        color = "🔴" if row['variacion_pct'] < 0 else "🟢"
                        st.markdown(f"{color} **{row['patente']}** - Variación: {row['variacion_pct']:.1f}% "
                                  f"(Actual: {row['rendimiento']:.2f} km/l)")
            
            if df_bajo_rend.empty and cargas_frecuentes.empty and variaciones_extremas.empty:
                st.success("✅ No se detectaron anomalías significativas")
        
        finally:
            conn.close()


if __name__ == "__main__":
    modulo_combustible()