# -*- coding: utf-8 -*-
# views/dashboard_avanzado.py - DASHBOARD CON ANÁLISIS AVANZADO

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from utils.helpers import get_db_connection

def mostrar_dashboard_avanzado():
    """Dashboard ejecutivo con análisis avanzado de la flota"""
    
    st.header("📊 Análisis Avanzado de Flota")
    st.caption("Métricas avanzadas y análisis predictivo")
    
    conn = get_db_connection()
    
    # =================================
    # 1. ANÁLISIS DE COSTOS
    # =================================
    st.subheader("💰 Análisis de Costos por Vehículo")
    
    try:
        df_costos = pd.read_sql_query("""
            SELECT 
                v.patente,
                v.tipo,
                v.marca,
                v.modelo,
                COALESCE(SUM(m.costo), 0) as costo_mantenimiento,
                COALESCE(SUM(c.costo_total), 0) as costo_combustible,
                COALESCE(SUM(m.costo), 0) + COALESCE(SUM(c.costo_total), 0) as costo_total,
                v.km_actual
            FROM vehiculos v
            LEFT JOIN mantenimientos m ON v.id = m.vehiculo_id
            LEFT JOIN combustible c ON v.id = c.vehiculo_id
            WHERE v.estado = 'activo'
            GROUP BY v.id
            ORDER BY costo_total DESC
        """, conn)
        
        if not df_costos.empty:
            # Calcular costo por km
            df_costos['costo_por_km'] = df_costos.apply(
                lambda row: row['costo_total'] / row['km_actual'] if row['km_actual'] > 0 else 0,
                axis=1
            )
            
            # Gráfico de costos totales
            col1, col2 = st.columns(2)
            
            with col1:
                fig_costos = px.bar(
                    df_costos.head(10),
                    x='patente',
                    y=['costo_mantenimiento', 'costo_combustible'],
                    title='Top 10 Unidades por Costo Total',
                    labels={'value': 'Costo ($ARS)', 'variable': 'Tipo'},
                    barmode='stack',
                    color_discrete_map={
                        'costo_mantenimiento': '#ff6b6b',
                        'costo_combustible': '#4ecdc4'
                    }
                )
                fig_costos.update_layout(height=400)
                st.plotly_chart(fig_costos, use_container_width=True)
            
            with col2:
                fig_costo_km = px.bar(
                    df_costos.nlargest(10, 'costo_por_km'),
                    x='patente',
                    y='costo_por_km',
                    title='Costo por Kilómetro (Top 10)',
                    labels={'costo_por_km': 'Costo/Km ($ARS)'},
                    color='costo_por_km',
                    color_continuous_scale='Reds'
                )
                fig_costo_km.update_layout(height=400)
                st.plotly_chart(fig_costo_km, use_container_width=True)
            
            # Tabla resumen
            st.dataframe(
                df_costos[['patente', 'tipo', 'costo_mantenimiento', 'costo_combustible', 'costo_total', 'costo_por_km']].round(2),
                use_container_width=True,
                hide_index=True
            )
    
    finally:
        pass
    
    st.divider()
    
    # =================================
    # 2. ANÁLISIS DE FALLAS Y CONFIABILIDAD
    # =================================
    st.subheader("⚠️ Análisis de Fallas y Confiabilidad")
    
    try:
        df_fallas = pd.read_sql_query("""
            SELECT 
                v.patente,
                v.tipo,
                COUNT(f.id) as total_fallas,
                SUM(CASE WHEN f.gravedad = 'critica' THEN 1 ELSE 0 END) as fallas_criticas,
                SUM(f.tiempo_inmovilizado_hrs) as horas_inmovilizado,
                SUM(f.costo_reparacion) as costo_reparaciones
            FROM vehiculos v
            LEFT JOIN fallas f ON v.id = f.vehiculo_id
            WHERE v.estado IN ('activo', 'en_reparacion')
            GROUP BY v.id
            HAVING total_fallas > 0
            ORDER BY total_fallas DESC
        """, conn)
        
        if not df_fallas.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Ranking de unidades más problemáticas
                fig_fallas = px.bar(
                    df_fallas.head(10),
                    x='patente',
                    y='total_fallas',
                    title='Unidades con Más Fallas (Top 10)',
                    labels={'total_fallas': 'Cantidad de Fallas'},
                    color='fallas_criticas',
                    color_continuous_scale='Reds'
                )
                fig_fallas.update_layout(height=400)
                st.plotly_chart(fig_fallas, use_container_width=True)
            
            with col2:
                # Tiempo de inmovilización
                fig_inmov = px.bar(
                    df_fallas.nlargest(10, 'horas_inmovilizado'),
                    x='patente',
                    y='horas_inmovilizado',
                    title='Tiempo de Inmovilización (Top 10)',
                    labels={'horas_inmovilizado': 'Horas Inmovilizado'},
                    color='horas_inmovilizado',
                    color_continuous_scale='Oranges'
                )
                fig_inmov.update_layout(height=400)
                st.plotly_chart(fig_inmov, use_container_width=True)
            
            # Resumen de unidades más problemáticas
            st.warning("⚠️ **Unidades que requieren atención especial:**")
            unidades_criticas = df_fallas[df_fallas['fallas_criticas'] > 0].head(5)
            for _, row in unidades_criticas.iterrows():
                st.markdown(f"🔴 **{row['patente']}** - {row['total_fallas']} fallas totales ({row['fallas_criticas']} críticas) | {row['horas_inmovilizado']:.0f} hrs inmovilizado | ${row['costo_reparaciones']:,.2f} en reparaciones")
        
        else:
            st.success("✅ ¡Excelente! No hay fallas registradas en la flota.")
    
    finally:
        pass
    
    st.divider()
    
    # =================================
    # 3. ANÁLISIS DE RENDIMIENTO DE COMBUSTIBLE
    # =================================
    st.subheader("⛽ Análisis de Rendimiento de Combustible")
    
    try:
        df_rendimiento = pd.read_sql_query("""
            SELECT 
                v.patente,
                v.tipo,
                AVG(c.rendimiento) as rendimiento_promedio,
                MIN(c.rendimiento) as rendimiento_minimo,
                MAX(c.rendimiento) as rendimiento_maximo,
                SUM(c.litros) as total_litros,
                SUM(c.costo_total) as total_gastado
            FROM vehiculos v
            JOIN combustible c ON v.id = c.vehiculo_id
            WHERE c.rendimiento IS NOT NULL
            GROUP BY v.id
            ORDER BY rendimiento_promedio DESC
        """, conn)
        
        if not df_rendimiento.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Mejor rendimiento
                fig_mejor_rend = px.bar(
                    df_rendimiento.head(10),
                    x='patente',
                    y='rendimiento_promedio',
                    title='Mejor Rendimiento (Top 10)',
                    labels={'rendimiento_promedio': 'Km/Litro'},
                    color='rendimiento_promedio',
                    color_continuous_scale='Greens'
                )
                fig_mejor_rend.update_layout(height=400)
                st.plotly_chart(fig_mejor_rend, use_container_width=True)
            
            with col2:
                # Peor rendimiento
                fig_peor_rend = px.bar(
                    df_rendimiento.tail(10),
                    x='patente',
                    y='rendimiento_promedio',
                    title='Menor Rendimiento (Bottom 10)',
                    labels={'rendimiento_promedio': 'Km/Litro'},
                    color='rendimiento_promedio',
                    color_continuous_scale='Reds'
                )
                fig_peor_rend.update_layout(height=400)
                st.plotly_chart(fig_peor_rend, use_container_width=True)
            
            # Gasto total por unidad
            fig_gasto = px.pie(
                df_rendimiento.head(10),
                values='total_gastado',
                names='patente',
                title='Distribución del Gasto en Combustible (Top 10)'
            )
            fig_gasto.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_gasto, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(
                df_rendimiento[['patente', 'tipo', 'rendimiento_promedio', 'rendimiento_minimo', 'rendimiento_maximo', 'total_litros', 'total_gastado']].round(2),
                use_container_width=True,
                hide_index=True
            )
    
    finally:
        pass
    
    st.divider()
    
    # =================================
    # 4. TENDENCIAS TEMPORALES
    # =================================
    st.subheader("📈 Tendencias de Mantenimiento")
    
    try:
        df_tendencia = pd.read_sql_query("""
            SELECT 
                DATE(fecha) as fecha,
                COUNT(*) as cantidad_mantenimientos,
                SUM(costo) as costo_total
            FROM mantenimientos
            WHERE fecha >= DATE('now', '-6 months')
            GROUP BY DATE(fecha)
            ORDER BY fecha
        """, conn)
        
        if not df_tendencia.empty:
            df_tendencia['fecha'] = pd.to_datetime(df_tendencia['fecha'])
            
            fig_tendencia = go.Figure()
            
            fig_tendencia.add_trace(go.Scatter(
                x=df_tendencia['fecha'],
                y=df_tendencia['cantidad_mantenimientos'],
                mode='lines+markers',
                name='Cantidad de Mantenimientos',
                line=dict(color='#4ecdc4', width=3),
                yaxis='y'
            ))
            
            fig_tendencia.add_trace(go.Scatter(
                x=df_tendencia['fecha'],
                y=df_tendencia['costo_total'],
                mode='lines+markers',
                name='Costo Total ($ARS)',
                line=dict(color='#ff6b6b', width=3),
                yaxis='y2'
            ))
            
            fig_tendencia.update_layout(
                title='Evolución de Mantenimientos (Últimos 6 Meses)',
                xaxis=dict(title='Fecha'),
                yaxis=dict(title='Cantidad', side='left'),
                yaxis2=dict(title='Costo ($ARS)', overlaying='y', side='right'),
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_tendencia, use_container_width=True)
    
    finally:
        pass
    
    st.divider()
    
    # =================================
    # 5. INDICADORES DE CUMPLIMIENTO
    # =================================
    st.subheader("✅ Indicadores de Cumplimiento")
    
    try:
        # Cumplimiento documental de vehículos
        total_docs = conn.execute("""
            SELECT COUNT(*) FROM vencimientos v
            JOIN vehiculos ve ON v.vehiculo_id = ve.id
            WHERE ve.estado = 'activo'
        """).fetchone()[0]
        
        docs_vencidos = conn.execute("""
            SELECT COUNT(*) FROM vencimientos v
            JOIN vehiculos ve ON v.vehiculo_id = ve.id
            WHERE ve.estado = 'activo' AND v.fecha_vencimiento < date('now')
        """).fetchone()[0]
        
        cumpl_docs = 100 if total_docs == 0 else round((total_docs - docs_vencidos) / total_docs * 100, 1)
        
        # Cumplimiento de mantenimientos preventivos
        mant_total = conn.execute("""
            SELECT COUNT(*) FROM mantenimientos m
            JOIN vehiculos v ON m.vehiculo_id = v.id
            WHERE v.estado = 'activo' AND m.prox_km IS NOT NULL
        """).fetchone()[0]
        
        mant_vencidos = conn.execute("""
            SELECT COUNT(*) FROM mantenimientos m
            JOIN vehiculos v ON m.vehiculo_id = v.id
            WHERE v.estado = 'activo' 
            AND m.prox_km IS NOT NULL 
            AND v.km_actual IS NOT NULL
            AND (m.prox_km - v.km_actual) < 0
        """).fetchone()[0]
        
        cumpl_mant = 100 if mant_total == 0 else round((mant_total - mant_vencidos) / mant_total * 100, 1)
        
        # Gráfico de gauge para cumplimiento
        col1, col2 = st.columns(2)
        
        with col1:
            fig_gauge_docs = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=cumpl_docs,
                title={'text': "Cumplimiento Documental"},
                delta={'reference': 100, 'increasing': {'color': "green"}},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen" if cumpl_docs >= 90 else "orange" if cumpl_docs >= 70 else "red"},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 90], 'color': "lightyellow"},
                        {'range': [90, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge_docs.update_layout(height=300)
            st.plotly_chart(fig_gauge_docs, use_container_width=True)
        
        with col2:
            fig_gauge_mant = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=cumpl_mant,
                title={'text': "Cumplimiento Mantenimientos"},
                delta={'reference': 100, 'increasing': {'color': "green"}},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkgreen" if cumpl_mant >= 90 else "orange" if cumpl_mant >= 70 else "red"},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 90], 'color': "lightyellow"},
                        {'range': [90, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge_mant.update_layout(height=300)
            st.plotly_chart(fig_gauge_mant, use_container_width=True)
        
        # Interpretación
        if cumpl_docs >= 90 and cumpl_mant >= 90:
            st.success("✅ **Excelente:** La flota mantiene altos estándares de cumplimiento.")
        elif cumpl_docs < 70 or cumpl_mant < 70:
            st.error("🚨 **Crítico:** Se requiere acción inmediata para mejorar el cumplimiento.")
        else:
            st.warning("⚠️ **Atención:** Hay margen de mejora en el cumplimiento de la flota.")
    
    finally:
        conn.close()
    
    st.divider()
    
    # =================================
    # 6. MATRIZ DE DISPONIBILIDAD
    # =================================
    st.subheader("🎯 Matriz de Disponibilidad de Flota")
    
    conn = get_db_connection()
    try:
        df_disponibilidad = pd.read_sql_query("""
            SELECT 
                tipo,
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'activo' THEN 1 ELSE 0 END) as activos,
                SUM(CASE WHEN estado = 'en_reparacion' THEN 1 ELSE 0 END) as en_reparacion,
                SUM(CASE WHEN estado = 'detenido' THEN 1 ELSE 0 END) as detenidos
            FROM vehiculos
            WHERE estado != 'baja'
            GROUP BY tipo
        """, conn)
        
        if not df_disponibilidad.empty:
            df_disponibilidad['disponibilidad_pct'] = (df_disponibilidad['activos'] / df_disponibilidad['total'] * 100).round(1)
            
            fig_matriz = go.Figure()
            
            fig_matriz.add_trace(go.Bar(
                name='Activos',
                x=df_disponibilidad['tipo'],
                y=df_disponibilidad['activos'],
                marker_color='green'
            ))
            
            fig_matriz.add_trace(go.Bar(
                name='En Reparación',
                x=df_disponibilidad['tipo'],
                y=df_disponibilidad['en_reparacion'],
                marker_color='orange'
            ))
            
            fig_matriz.add_trace(go.Bar(
                name='Detenidos',
                x=df_disponibilidad['tipo'],
                y=df_disponibilidad['detenidos'],
                marker_color='red'
            ))
            
            fig_matriz.update_layout(
                barmode='stack',
                title='Disponibilidad por Tipo de Vehículo',
                xaxis_title='Tipo de Vehículo',
                yaxis_title='Cantidad',
                height=400
            )
            
            st.plotly_chart(fig_matriz, use_container_width=True)
            
            # Tabla resumen
            st.dataframe(
                df_disponibilidad[['tipo', 'total', 'activos', 'en_reparacion', 'detenidos', 'disponibilidad_pct']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "tipo": "Tipo",
                    "total": "Total",
                    "activos": "Activos",
                    "en_reparacion": "En Reparación",
                    "detenidos": "Detenidos",
                    "disponibilidad_pct": st.column_config.ProgressColumn(
                        "Disponibilidad %",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )
    
    finally:
        conn.close()
    
    st.divider()
    
    # =================================
    # 7. PROYECCIONES Y PREDICCIONES
    # =================================
    st.subheader("🔮 Proyecciones y Predicciones")
    
    conn = get_db_connection()
    try:
        # Proyección de costos del próximo mes
        df_costos_mes = pd.read_sql_query("""
            SELECT 
                strftime('%Y-%m', fecha) as mes,
                SUM(costo) as costo_total
            FROM mantenimientos
            WHERE fecha >= DATE('now', '-6 months')
            GROUP BY strftime('%Y-%m', fecha)
            ORDER BY mes
        """, conn)
        
        if len(df_costos_mes) >= 3:
            promedio_mensual = df_costos_mes['costo_total'].mean()
            tendencia = df_costos_mes['costo_total'].iloc[-1] - df_costos_mes['costo_total'].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            col1.metric(
                "💰 Promedio Mensual",
                f"${promedio_mensual:,.2f}",
                delta=f"Últimos 6 meses"
            )
            
            col2.metric(
                "📊 Proyección Próximo Mes",
                f"${promedio_mensual * 1.1:,.2f}",
                delta="+10% estimado"
            )
            
            col3.metric(
                "📈 Tendencia",
                "Creciente" if tendencia > 0 else "Decreciente",
                delta=f"${abs(tendencia):,.2f}",
                delta_color="inverse" if tendencia > 0 else "normal"
            )
            
            # Gráfico de proyección
            fig_proyeccion = go.Figure()
            
            fig_proyeccion.add_trace(go.Scatter(
                x=df_costos_mes['mes'],
                y=df_costos_mes['costo_total'],
                mode='lines+markers',
                name='Histórico',
                line=dict(color='#4ecdc4', width=3)
            ))
            
            # Línea de proyección
            ultimo_mes = df_costos_mes['mes'].iloc[-1]
            proximo_mes = pd.to_datetime(ultimo_mes) + pd.DateOffset(months=1)
            proximo_mes_str = proximo_mes.strftime('%Y-%m')
            
            fig_proyeccion.add_trace(go.Scatter(
                x=[ultimo_mes, proximo_mes_str],
                y=[df_costos_mes['costo_total'].iloc[-1], promedio_mensual * 1.1],
                mode='lines+markers',
                name='Proyección',
                line=dict(color='#ff6b6b', width=3, dash='dash')
            ))
            
            fig_proyeccion.update_layout(
                title='Costos de Mantenimiento - Histórico y Proyección',
                xaxis_title='Mes',
                yaxis_title='Costo ($ARS)',
                height=400
            )
            
            st.plotly_chart(fig_proyeccion, use_container_width=True)
        
        else:
            st.info("ℹ️ Se necesitan al menos 3 meses de datos para generar proyecciones.")
    
    finally:
        conn.close()
    
    st.divider()
    
    # =================================
    # 8. ALERTAS Y RECOMENDACIONES
    # =================================
    st.subheader("💡 Recomendaciones del Sistema")
    
    conn = get_db_connection()
    try:
        recomendaciones = []
        
        # Verificar unidades con bajo rendimiento
        df_bajo_rend = pd.read_sql_query("""
            SELECT v.patente, AVG(c.rendimiento) as rend_prom
            FROM vehiculos v
            JOIN combustible c ON v.id = c.vehiculo_id
            WHERE c.rendimiento IS NOT NULL
            GROUP BY v.id
            HAVING rend_prom < (SELECT AVG(rendimiento) * 0.8 FROM combustible WHERE rendimiento IS NOT NULL)
        """, conn)
        
        if not df_bajo_rend.empty:
            recomendaciones.append({
                "tipo": "⚠️ Rendimiento",
                "descripcion": f"{len(df_bajo_rend)} unidades tienen rendimiento 20% inferior al promedio",
                "accion": "Revisar filtros de aire, inyectores y presión de neumáticos"
            })
        
        # Verificar unidades con muchas fallas
        df_fallas_rep = pd.read_sql_query("""
            SELECT v.patente, COUNT(f.id) as cant_fallas
            FROM vehiculos v
            JOIN fallas f ON v.id = f.vehiculo_id
            WHERE f.fecha >= DATE('now', '-3 months')
            GROUP BY v.id
            HAVING cant_fallas >= 3
        """, conn)
        
        if not df_fallas_rep.empty:
            recomendaciones.append({
                "tipo": "🔴 Fallas Recurrentes",
                "descripcion": f"{len(df_fallas_rep)} unidades con 3+ fallas en los últimos 3 meses",
                "accion": "Realizar diagnóstico profundo y considerar reemplazo de componentes críticos"
            })
        
        # Verificar documentación próxima a vencer
        docs_proximos = conn.execute("""
            SELECT COUNT(*) FROM vencimientos v
            JOIN vehiculos ve ON v.vehiculo_id = ve.id
            WHERE ve.estado = 'activo'
            AND julianday(v.fecha_vencimiento) - julianday('now') BETWEEN 0 AND 15
        """).fetchone()[0]
        
        if docs_proximos > 0:
            recomendaciones.append({
                "tipo": "📅 Documentación",
                "descripcion": f"{docs_proximos} documentos vencen en los próximos 15 días",
                "accion": "Programar renovaciones con urgencia"
            })
        
        # Verificar mantenimientos atrasados
        mant_atrasados = conn.execute("""
            SELECT COUNT(*) FROM mantenimientos m
            JOIN vehiculos v ON m.vehiculo_id = v.id
            WHERE v.estado = 'activo'
            AND ((m.prox_km IS NOT NULL AND v.km_actual IS NOT NULL AND (m.prox_km - v.km_actual) < 0)
                 OR (m.prox_fecha IS NOT NULL AND m.prox_fecha < DATE('now')))
        """).fetchone()[0]
        
        if mant_atrasados > 0:
            recomendaciones.append({
                "tipo": "🔧 Mantenimientos",
                "descripcion": f"{mant_atrasados} mantenimientos preventivos atrasados",
                "accion": "Priorizar estos mantenimientos para evitar fallas mayores"
            })
        
        if recomendaciones:
            for rec in recomendaciones:
                with st.expander(f"{rec['tipo']} - {rec['descripcion']}"):
                    st.write(f"**Acción recomendada:** {rec['accion']}")
        else:
            st.success("✅ ¡Excelente! No hay recomendaciones urgentes en este momento.")
    
    finally:
        conn.close()


if __name__ == "__main__":
    mostrar_dashboard_avanzado()