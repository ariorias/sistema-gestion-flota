# -*- coding: utf-8 -*-
# views/conductor_detalle.py - FICHA COMPLETA DE CONDUCTOR

import streamlit as st
import pandas as pd
from datetime import date
from utils.helpers import get_db_connection, dias_hasta

def mostrar_ficha_conductor():
    """Muestra la ficha completa de un conductor con toda su documentación"""
    
    st.header("👨‍✈️ Ficha Completa de Conductor")
    
    conn = get_db_connection()
    try:
        df_cond = pd.read_sql_query("""
            SELECT c.*, v.patente 
            FROM conductores c
            LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.id
            ORDER BY c.nombre
        """, conn)
    finally:
        conn.close()
    
    if df_cond.empty:
        st.warning("⚠️ No hay conductores registrados.")
        return
    
    # Selector de conductor
    col1, col2 = st.columns([3, 1])
    with col1:
        conductor_sel = st.selectbox(
            "👤 Seleccionar Conductor",
            df_cond["nombre"].tolist(),
            format_func=lambda x: f"{x} - DNI: {df_cond[df_cond['nombre']==x]['dni'].iloc[0]}"
        )
    
    conductor_info = df_cond[df_cond["nombre"] == conductor_sel].iloc[0]
    
    with col2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # ========================================
    # INFORMACIÓN PERSONAL
    # ========================================
    st.subheader(f"📋 Información Personal: **{conductor_info['nombre']}**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("DNI", conductor_info['dni'])
    col2.metric("Teléfono", conductor_info['telefono'] or "No registrado")
    col3.metric("Email", conductor_info['email'] or "No registrado")
    
    # Estado del conductor
    estado = conductor_info['estado']
    if estado == 'activo':
        col4.markdown("**Estado:** 🟢 Activo")
    elif estado == 'suspendido':
        col4.markdown("**Estado:** 🔴 Suspendido")
    else:
        col4.markdown("**Estado:** ⚪ Inactivo")
    
    col1, col2 = st.columns(2)
    col1.metric("🚛 Vehículo Asignado", conductor_info['patente'] or "Sin asignar")
    col2.metric("📅 Fecha de Nacimiento", conductor_info['fecha_nacimiento'] or "No registrada")
    
    if conductor_info['observaciones']:
        st.info(f"📝 **Observaciones:** {conductor_info['observaciones']}")
    
    st.divider()
    
    # ========================================
    # DOCUMENTACIÓN Y HABILITACIONES
    # ========================================
    st.subheader("📄 Documentación y Habilitaciones")
    
    docs = [
        ("Licencia de Conducir", conductor_info['licencia_venc'], conductor_info['licencia_tipo']),
        ("Cargas Peligrosas", conductor_info['licencia_cargas_peligrosas'], None),
        ("Examen Psicofísico", conductor_info['examen_psicofisico'], None),
        ("Curso IRAM", conductor_info['curso_iram'], None),
    ]
    
    docs_estado = []
    alerta_critica = False
    
    for doc_nombre, fecha_venc, tipo_extra in docs:
        if fecha_venc:
            dias = dias_hasta(fecha_venc)
            
            if dias < 0:
                icono = "🔴"
                estado = "VENCIDO"
                alerta_critica = True
            elif dias < 7:
                icono = "🟠"
                estado = "URGENTE"
                alerta_critica = True
            elif dias < 30:
                icono = "🟡"
                estado = "PRÓXIMO"
            else:
                icono = "🟢"
                estado = "VIGENTE"
            
            extra_info = f" ({tipo_extra})" if tipo_extra else ""
            
            docs_estado.append({
                "": icono,
                "Documento": doc_nombre + extra_info,
                "Vencimiento": fecha_venc,
                "Días Restantes": f"{dias} días",
                "Estado": estado
            })
        else:
            docs_estado.append({
                "": "⚪",
                "Documento": doc_nombre,
                "Vencimiento": "No registrado",
                "Días Restantes": "-",
                "Estado": "SIN DATOS"
            })
    
    if alerta_critica:
        st.error("🚨 **ALERTA CRÍTICA:** Este conductor tiene documentación vencida o por vencer.")
    
    df_docs = pd.DataFrame(docs_estado)
    st.dataframe(df_docs, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # ========================================
    # HISTORIAL DE CARGAS DE COMBUSTIBLE
    # ========================================
    st.subheader("⛽ Historial de Cargas de Combustible")
    
    conn = get_db_connection()
    try:
        df_comb = pd.read_sql_query("""
            SELECT 
                c.fecha,
                v.patente,
                c.km,
                c.litros,
                c.costo_total,
                c.rendimiento,
                c.estacion
            FROM combustible c
            JOIN vehiculos v ON c.vehiculo_id = v.id
            WHERE c.conductor_id = ?
            ORDER BY c.fecha DESC
            LIMIT 30
        """, conn, params=(conductor_info['id'],))
    finally:
        conn.close()
    
    if not df_comb.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_cargas = len(df_comb)
        total_litros = df_comb['litros'].sum()
        total_gastado = df_comb['costo_total'].sum()
        rend_prom = df_comb['rendimiento'].mean()
        
        col1.metric("📊 Total Cargas", total_cargas)
        col2.metric("⛽ Total Litros", f"{total_litros:.0f} L")
        col3.metric("💰 Total Gastado", f"${total_gastado:,.2f}")
        col4.metric("📈 Rendimiento Prom.", f"{rend_prom:.2f} km/l")
        
        with st.expander("📋 Ver Últimas 30 Cargas"):
            st.dataframe(df_comb, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No hay registros de combustible asociados a este conductor.")
    
    st.divider()
    
    # ========================================
    # ACCIONES RÁPIDAS
    # ========================================
    st.subheader("⚡ Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Enviar Recordatorio de Documentación", use_container_width=True):
            st.info("📧 Funcionalidad de envío de email en desarrollo...")
    
    with col2:
        if st.button("📄 Generar Reporte PDF", use_container_width=True):
            st.info("📄 Funcionalidad de reporte PDF en desarrollo...")
    
    with col3:
        if st.button("✏️ Editar Información", use_container_width=True):
            st.info("✏️ Modo de edición en desarrollo...")

if __name__ == "__main__":
    mostrar_ficha_conductor()