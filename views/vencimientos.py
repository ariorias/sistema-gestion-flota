# -*- coding: utf-8 -*-
# views/vencimientos.py - MÓDULO DE VENCIMIENTOS

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from utils.helpers import get_db_connection, dias_hasta

def modulo_vencimientos():
    """Módulo completo de gestión de vencimientos"""
    
    st.header("📅 Gestión de Vencimientos Documentales")
    
    tab1, tab2, tab3 = st.tabs(["➕ Registrar Vencimiento", "📋 Vencimientos Activos", "📊 Próximos a Vencer"])
    
    # ==========================================
    # TAB 1: REGISTRAR NUEVO VENCIMIENTO
    # ==========================================
    with tab1:
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("""
                SELECT id, patente, marca, modelo 
                FROM vehiculos 
                WHERE estado = 'activo' 
                ORDER BY patente
            """, conn)
        finally:
            conn.close()
        
        if df_veh.empty:
            st.warning("⚠️ No hay vehículos activos. Registre vehículos primero.")
            return
        
        patentes_dict = {f"{row['patente']} - {row['marca']} {row['modelo']}": row['id'] 
                        for _, row in df_veh.iterrows()}
        
        with st.form("nuevo_vencimiento"):
            st.subheader("📝 Registrar Nuevo Vencimiento")
            
            vehiculo_sel = st.selectbox("🚛 Vehículo", list(patentes_dict.keys()))
            
            col1, col2 = st.columns(2)
            
            tipo_doc = col1.selectbox("📄 Tipo de Documento", [
                "VTV",
                "Seguro",
                "Patente",
                "Cédula Verde",
                "Cédula Azul",
                "Habilitación Municipal",
                "Transporte de Cargas Peligrosas",
                "Matafuego - Vencimiento",
                "Matafuego - Recarga",
                "Sanitario",
                "SENASA",
                "Otro"
            ])
            
            if tipo_doc == "Otro":
                tipo_doc = col2.text_input("Especificar tipo")
            
            col1, col2, col3 = st.columns(3)
            
            fecha_venc = col1.date_input(
                "📅 Fecha de Vencimiento",
                value=date.today() + timedelta(days=30)
            )
            
            fecha_ultimo = col2.date_input(
                "📅 Última Renovación",
                value=date.today()
            )
            
            alerta_dias = col3.number_input(
                "🔔 Días de anticipación",
                min_value=1,
                max_value=180,
                value=30,
                help="Días antes del vencimiento para recibir alertas"
            )
            
            costo = st.number_input(
                "💰 Costo de Renovación (ARS)",
                min_value=0.0,
                step=1000.0,
                help="Costo estimado de la renovación"
            )
            
            observaciones = st.text_area(
                "📝 Observaciones",
                placeholder="Ej: Renovar en oficina central, requiere inspección previa, etc."
            )
            
            submitted = st.form_submit_button("💾 Guardar Vencimiento", use_container_width=True)
            
            if submitted and tipo_doc:
                veh_id = patentes_dict[vehiculo_sel]
                
                conn = get_db_connection()
                try:
                    conn.execute("""
                        INSERT INTO vencimientos 
                        (vehiculo_id, tipo, fecha_vencimiento, fecha_ultimo, 
                         alerta_dias, costo_renovacion, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (veh_id, tipo_doc, fecha_venc, fecha_ultimo, 
                         alerta_dias, costo if costo > 0 else None, observaciones))
                    conn.commit()
                    st.success(f"✅ Vencimiento de {tipo_doc} registrado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
                finally:
                    conn.close()
    
    # ==========================================
    # TAB 2: LISTADO COMPLETO
    # ==========================================
    with tab2:
        st.subheader("📋 Todos los Vencimientos Activos")
        
        conn = get_db_connection()
        try:
            df_venc = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    ve.tipo,
                    ve.fecha_vencimiento,
                    ve.fecha_ultimo,
                    ve.alerta_dias,
                    ve.costo_renovacion,
                    julianday(ve.fecha_vencimiento) - julianday('now') as dias_faltantes,
                    ve.observaciones
                FROM vencimientos ve
                JOIN vehiculos v ON ve.vehiculo_id = v.id
                WHERE v.estado = 'activo' AND ve.estado = 'activo'
                ORDER BY ve.fecha_vencimiento
            """, conn)
            
            if not df_venc.empty:
                # Agregar columna de estado visual
                def obtener_estado(dias):
                    if dias < 0:
                        return "🔴 VENCIDO"
                    elif dias < 7:
                        return "🟠 URGENTE"
                    elif dias < 30:
                        return "🟡 PRÓXIMO"
                    else:
                        return "🟢 VIGENTE"
                
                df_venc['Estado'] = df_venc['dias_faltantes'].apply(lambda x: obtener_estado(int(x)))
                df_venc['dias_faltantes'] = df_venc['dias_faltantes'].apply(lambda x: f"{int(x)} días")
                
                # Renombrar columnas para mejor visualización
                df_display = df_venc[[
                    'Estado', 'patente', 'tipo', 'fecha_vencimiento', 
                    'dias_faltantes', 'costo_renovacion', 'observaciones'
                ]].rename(columns={
                    'patente': 'Patente',
                    'tipo': 'Documento',
                    'fecha_vencimiento': 'Vencimiento',
                    'dias_faltantes': 'Días Restantes',
                    'costo_renovacion': 'Costo Renov.',
                    'observaciones': 'Observaciones'
                })
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtro_estado = st.multiselect(
                        "Filtrar por estado",
                        ["🔴 VENCIDO", "🟠 URGENTE", "🟡 PRÓXIMO", "🟢 VIGENTE"],
                        default=["🔴 VENCIDO", "🟠 URGENTE", "🟡 PRÓXIMO", "🟢 VIGENTE"]
                    )
                
                with col2:
                    patentes_unicas = df_display['Patente'].unique()
                    filtro_patente = st.multiselect(
                        "Filtrar por patente",
                        patentes_unicas,
                        default=patentes_unicas
                    )
                
                with col3:
                    tipos_unicos = df_display['Documento'].unique()
                    filtro_tipo = st.multiselect(
                        "Filtrar por tipo",
                        tipos_unicos,
                        default=tipos_unicos
                    )
                
                # Aplicar filtros
                df_filtrado = df_display[
                    (df_display['Estado'].isin(filtro_estado)) &
                    (df_display['Patente'].isin(filtro_patente)) &
                    (df_display['Documento'].isin(filtro_tipo))
                ]
                
                # Mostrar estadísticas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 Total", len(df_filtrado))
                col2.metric("🔴 Vencidos", len(df_filtrado[df_filtrado['Estado'] == "🔴 VENCIDO"]))
                col3.metric("🟠 Urgentes", len(df_filtrado[df_filtrado['Estado'] == "🟠 URGENTE"]))
                col4.metric("🟡 Próximos", len(df_filtrado[df_filtrado['Estado'] == "🟡 PRÓXIMO"]))
                
                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Costo Renov.": st.column_config.NumberColumn(
                            "Costo Renov.",
                            format="$ %.2f"
                        )
                    }
                )
                
                # Costo total de renovaciones próximas
                costo_total = df_filtrado[df_filtrado['Estado'].isin(["🔴 VENCIDO", "🟠 URGENTE"])]['Costo Renov.'].sum()
                if costo_total > 0:
                    st.info(f"💰 **Costo estimado de renovaciones urgentes:** ${costo_total:,.2f}")
                
            else:
                st.info("ℹ️ No hay vencimientos registrados")
        
        finally:
            conn.close()
    
    # ==========================================
    # TAB 3: PRÓXIMOS A VENCER (30 DÍAS)
    # ==========================================
    with tab3:
        st.subheader("⚠️ Documentos que Vencen en los Próximos 30 Días")
        
        conn = get_db_connection()
        try:
            df_proximos = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    v.marca,
                    v.modelo,
                    ve.tipo,
                    ve.fecha_vencimiento,
                    julianday(ve.fecha_vencimiento) - julianday('now') as dias_faltantes,
                    ve.costo_renovacion,
                    ve.observaciones
                FROM vencimientos ve
                JOIN vehiculos v ON ve.vehiculo_id = v.id
                WHERE v.estado = 'activo' 
                AND ve.estado = 'activo'
                AND julianday(ve.fecha_vencimiento) - julianday('now') BETWEEN 0 AND 30
                ORDER BY dias_faltantes
            """, conn)
            
            if not df_proximos.empty:
                st.warning(f"⚠️ **{len(df_proximos)} documentos requieren atención inmediata**")
                
                for idx, row in df_proximos.iterrows():
                    dias = int(row['dias_faltantes'])
                    
                    if dias < 0:
                        color = "🔴"
                        estado = "VENCIDO"
                    elif dias < 7:
                        color = "🟠"
                        estado = "URGENTE"
                    else:
                        color = "🟡"
                        estado = "PRÓXIMO"
                    
                    with st.expander(f"{color} {row['patente']} - {row['tipo']} ({dias} días) - {estado}"):
                        col1, col2 = st.columns(2)
                        
                        col1.write(f"**Vehículo:** {row['marca']} {row['modelo']}")
                        col1.write(f"**Vencimiento:** {row['fecha_vencimiento']}")
                        
                        col2.write(f"**Días restantes:** {dias}")
                        if row['costo_renovacion']:
                            col2.write(f"**Costo estimado:** ${row['costo_renovacion']:,.2f}")
                        
                        if row['observaciones']:
                            st.info(f"📝 {row['observaciones']}")
                        
                        # Botón de acción rápida
                        if st.button(f"✅ Marcar como Renovado", key=f"renovar_{idx}"):
                            st.info("🔄 Funcionalidad en desarrollo...")
            
            else:
                st.success("✅ ¡Excelente! No hay documentos próximos a vencer en los próximos 30 días")
        
        finally:
            conn.close()


if __name__ == "__main__":
    modulo_vencimientos()