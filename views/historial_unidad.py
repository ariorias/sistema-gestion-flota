# -*- coding: utf-8 -*-
# views/historial_unidad.py - VISTA HISTORIAL COMPLETO TIPO CHECKLIST

import streamlit as st
import pandas as pd
from datetime import date
from utils.helpers import get_db_connection

def vista_historial_unidad():
    """Vista tipo checklist con TODO el historial de mantenimiento de una unidad"""
    
    st.header("📋 Historial Completo de Mantenimiento por Unidad")
    
    conn = get_db_connection()
    try:
        df_veh = pd.read_sql_query("""
            SELECT id, patente, marca, modelo, tipo, km_actual
            FROM vehiculos 
            WHERE estado != 'baja'
            ORDER BY patente
        """, conn)
    finally:
        conn.close()
    
    if df_veh.empty:
        st.warning("⚠️ No hay vehículos registrados")
        return
    
    # Selector de vehículo
    col1, col2 = st.columns([3, 1])
    
    with col1:
        vehiculo_sel = st.selectbox(
            "🚛 Seleccionar Unidad",
            df_veh['patente'].tolist(),
            format_func=lambda x: f"{x} - {df_veh[df_veh['patente']==x]['marca'].iloc[0]} {df_veh[df_veh['patente']==x]['modelo'].iloc[0]}"
        )
    
    veh_data = df_veh[df_veh['patente'] == vehiculo_sel].iloc[0]
    veh_id = veh_data['id']
    
    with col2:
        if st.button("🖨️ Imprimir Historial", use_container_width=True):
            st.info("🔄 Función de impresión en desarrollo...")
    
    # ==========================================
    # INFORMACIÓN DEL VEHÍCULO
    # ==========================================
    st.subheader(f"📊 Historial: **{veh_data['patente']}**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Marca/Modelo", f"{veh_data['marca']} {veh_data['modelo']}")
    col2.metric("Tipo", veh_data['tipo'].title())
    col3.metric("Kilometraje Actual", f"{veh_data['km_actual']:,} km")
    
    st.divider()
    
    # ==========================================
    # TABLA DE MANTENIMIENTOS - FORMATO CHECKLIST
    # ==========================================
    st.subheader("🔧 Registro de Mantenimientos")
    
    conn = get_db_connection()
    try:
        # Obtener TODOS los mantenimientos de esta unidad
        df_mant = pd.read_sql_query("""
            SELECT 
                tipo,
                fecha,
                km,
                prox_km,
                prox_fecha,
                costo,
                taller,
                observaciones
            FROM mantenimientos
            WHERE vehiculo_id = ?
            ORDER BY tipo, fecha DESC
        """, conn, params=(veh_id,))
        
        if not df_mant.empty:
            # Agrupar por tipo de mantenimiento
            tipos_mant = df_mant['tipo'].unique()
            
            # Crear la tabla tipo checklist
            datos_tabla = []
            
            for tipo in sorted(tipos_mant):
                df_tipo = df_mant[df_mant['tipo'] == tipo].sort_values('fecha', ascending=False)
                
                # Obtener último mantenimiento
                ultimo = df_tipo.iloc[0]
                
                # Calcular estado
                if ultimo['prox_km'] and veh_data['km_actual']:
                    km_faltantes = ultimo['prox_km'] - veh_data['km_actual']
                    if km_faltantes < 0:
                        estado_km = "🔴 VENCIDO"
                    elif km_faltantes < 1000:
                        estado_km = "🟠 URGENTE"
                    elif km_faltantes < 2000:
                        estado_km = "🟡 PRÓXIMO"
                    else:
                        estado_km = "🟢 OK"
                else:
                    estado_km = "-"
                    km_faltantes = 0
                
                # Armar fila
                fila = {
                    "Item": tipo,
                    "Último Cambio": ultimo['fecha'],
                    "KM del Cambio": f"{ultimo['km']:,}" if ultimo['km'] else "-",
                    "Próximo KM": f"{ultimo['prox_km']:,}" if ultimo['prox_km'] else "-",
                    "Faltan (km)": f"{km_faltantes:,}" if km_faltantes else "-",
                    "Estado": estado_km,
                    "Próxima Fecha": ultimo['prox_fecha'] if ultimo['prox_fecha'] else "-",
                    "Taller": ultimo['taller'] if ultimo['taller'] else "-",
                    "Veces Cambiado": len(df_tipo)
                }
                
                datos_tabla.append(fila)
            
            # Mostrar tabla
            df_checklist = pd.DataFrame(datos_tabla)
            
            st.dataframe(
                df_checklist,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                    "Veces Cambiado": st.column_config.NumberColumn("Veces", width="small")
                }
            )
            
            # ==========================================
            # DETALLE EXPANDIBLE POR ITEM
            # ==========================================
            st.subheader("📜 Historial Detallado por Componente")
            
            for tipo in sorted(tipos_mant):
                df_tipo = df_mant[df_mant['tipo'] == tipo].sort_values('fecha', ascending=False)
                
                with st.expander(f"🔧 {tipo} ({len(df_tipo)} registros)"):
                    for idx, row in df_tipo.iterrows():
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.write(f"**Fecha:** {row['fecha']}")
                        col2.write(f"**KM:** {row['km']:,}" if row['km'] else "**KM:** -")
                        col3.write(f"**Costo:** ${row['costo']:,.2f}" if row['costo'] else "**Costo:** -")
                        col4.write(f"**Taller:** {row['taller']}" if row['taller'] else "**Taller:** -")
                        
                        if row['observaciones']:
                            st.caption(f"📝 {row['observaciones']}")
                        
                        st.divider()
            
            # ==========================================
            # RESUMEN ESTADÍSTICO
            # ==========================================
            st.subheader("📊 Resumen Estadístico")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_mantenimientos = len(df_mant)
            costo_total = df_mant['costo'].sum()
            costo_promedio = df_mant['costo'].mean()
            items_diferentes = len(tipos_mant)
            
            col1.metric("Total Mantenimientos", total_mantenimientos)
            col2.metric("Componentes Diferentes", items_diferentes)
            col3.metric("Costo Total Histórico", f"${costo_total:,.2f}")
            col4.metric("Costo Promedio", f"${costo_promedio:,.2f}")
            
            # Gráfico de costos por tipo
            import plotly.express as px
            
            df_costos_tipo = df_mant.groupby('tipo')['costo'].sum().reset_index()
            df_costos_tipo = df_costos_tipo.sort_values('costo', ascending=False).head(10)
            
            fig = px.bar(
                df_costos_tipo,
                x='tipo',
                y='costo',
                title='Top 10 - Costos por Tipo de Mantenimiento',
                labels={'costo': 'Costo Total ($)', 'tipo': 'Tipo de Mantenimiento'},
                color='costo',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("ℹ️ No hay mantenimientos registrados para esta unidad")
            st.warning("💡 Registre el primer mantenimiento en la sección '🔧 Mantenimientos'")
    
    finally:
        conn.close()
    
    # ==========================================
    # BOTÓN PARA REGISTRAR NUEVO MANTENIMIENTO
    # ==========================================
    st.divider()
    
    if st.button("➕ Registrar Nuevo Mantenimiento para esta Unidad", use_container_width=True, type="primary"):
        st.info("🔄 Redirigiendo a módulo de mantenimientos...")
        # Aquí se puede implementar navegación o abrir modal


if __name__ == "__main__":
    vista_historial_unidad()