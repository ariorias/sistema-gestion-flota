# -*- coding: utf-8 -*-
# views/unidad_detalle.py - FICHA COMPLETA DE VEHÍCULO

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.helpers import get_db_connection, dias_hasta

def mostrar_ficha_unidad():
    """Muestra la ficha técnica completa de un vehículo con historial preventivo"""
    
    st.header("🔍 Ficha Técnica Completa de Unidad")
    
    conn = get_db_connection()
    try:
        df_veh = pd.read_sql_query(
            "SELECT id, patente, marca, modelo, tipo FROM vehiculos ORDER BY patente", 
            conn
        )
    finally:
        conn.close()
    
    if df_veh.empty:
        st.warning("⚠️ No hay vehículos registrados.")
        return
    
    # Selector de vehículo
    col1, col2 = st.columns([3, 1])
    with col1:
        patente_sel = st.selectbox(
            "🚛 Seleccionar Unidad",
            df_veh["patente"].tolist(),
            format_func=lambda x: f"{x} - {df_veh[df_veh['patente']==x]['marca'].iloc[0]} {df_veh[df_veh['patente']==x]['modelo'].iloc[0]}"
        )
    
    veh_id = df_veh[df_veh["patente"] == patente_sel]["id"].iloc[0]
    
    with col2:
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()
    
    # ========================================
    # INFORMACIÓN GENERAL DEL VEHÍCULO
    # ========================================
    conn = get_db_connection()
    try:
        veh_info = conn.execute("""
            SELECT * FROM vehiculos WHERE id = ?
        """, (veh_id,)).fetchone()
        
        st.subheader(f"📋 Información General: **{veh_info['patente']}**")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Marca/Modelo", f"{veh_info['marca']} {veh_info['modelo']}")
        col2.metric("Año", veh_info['anio'])
        col3.metric("Tipo", veh_info['tipo'].title())
        
        # Estado con color
        estado = veh_info['estado']
        if estado == 'activo':
            col4.markdown("**Estado:** 🟢 Activo")
        elif estado == 'en_reparacion':
            col4.markdown("**Estado:** 🟡 En Reparación")
        else:
            col4.markdown("**Estado:** 🔴 Detenido")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📍 Centro Operativo", veh_info['centro_operativo'] or "No asignado")
        col2.metric("🛣️ Kilometraje Actual", f"{veh_info['km_actual']:,} km")
        
        # Calcular promedio km/día
        km_diarios = conn.execute("""
            SELECT AVG(diferencia_km) as prom_km_dia FROM (
                SELECT 
                    (km - LAG(km) OVER (ORDER BY fecha)) / 
                    (julianday(fecha) - julianday(LAG(fecha) OVER (ORDER BY fecha))) as diferencia_km
                FROM combustible
                WHERE vehiculo_id = ? AND km IS NOT NULL
            ) WHERE diferencia_km > 0 AND diferencia_km < 1000
        """, (veh_id,)).fetchone()
        
        prom_km = km_diarios['prom_km_dia'] if km_diarios and km_diarios['prom_km_dia'] else 0
        col3.metric("📊 Promedio km/día", f"{prom_km:.0f} km" if prom_km > 0 else "Sin datos")
        
        st.divider()
        
        # ========================================
        # MANTENIMIENTOS PREVENTIVOS
        # ========================================
        st.subheader("🔧 Historial de Mantenimientos Preventivos")
        
        # Definir mantenimientos críticos
        mantenimientos_criticos = [
            ("Aceite de Motor", 10000, 180),
            ("Filtro de Aceite", 10000, 180),
            ("Filtro de Aire", 20000, 365),
            ("Filtro de Gasoil", 20000, 365),
            ("Filtro Separador de Agua", 15000, 180),
            ("Pastillas de Freno", 30000, 730),
            ("Aceite de Caja", 40000, 730),
            ("Aceite de Diferencial", 40000, 730),
        ]
        
        df_mant_hist = pd.read_sql_query("""
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
            ORDER BY fecha DESC
        """, conn, params=(veh_id,))
        
        if not df_mant_hist.empty:
            # Crear tabla resumen de estado de mantenimientos
            estado_mant = []
            
            for mant_tipo, km_intervalo, dias_intervalo in mantenimientos_criticos:
                # Buscar el último mantenimiento de este tipo
                ultimo = df_mant_hist[df_mant_hist['tipo'].str.contains(mant_tipo, case=False, na=False)]
                
                if not ultimo.empty:
                    ultimo = ultimo.iloc[0]
                    ultimo_km = ultimo['km']
                    ultimo_fecha = ultimo['fecha']
                    prox_km = ultimo['prox_km'] if ultimo['prox_km'] else ultimo_km + km_intervalo
                    prox_fecha = ultimo['prox_fecha'] if ultimo['prox_fecha'] else (
                        pd.to_datetime(ultimo_fecha) + timedelta(days=dias_intervalo)
                    ).strftime('%Y-%m-%d')
                    
                    # Calcular días y km faltantes
                    km_faltantes = prox_km - veh_info['km_actual']
                    dias_faltantes = dias_hasta(prox_fecha)
                    
                    # Determinar estado
                    if km_faltantes < 0 or dias_faltantes < 0:
                        icono = "🔴"
                        estado_txt = "VENCIDO"
                    elif km_faltantes < 1000 or dias_faltantes < 15:
                        icono = "🟠"
                        estado_txt = "URGENTE"
                    elif km_faltantes < 2000 or dias_faltantes < 30:
                        icono = "🟡"
                        estado_txt = "PRÓXIMO"
                    else:
                        icono = "🟢"
                        estado_txt = "OK"
                    
                    estado_mant.append({
                        "Estado": icono,
                        "Mantenimiento": mant_tipo,
                        "Último Cambio": f"{ultimo_km:,} km ({ultimo_fecha})",
                        "Próximo": f"{prox_km:,} km ({prox_fecha})",
                        "Faltan": f"{km_faltantes:,} km / {dias_faltantes} días",
                        "Condición": estado_txt
                    })
                else:
                    # Nunca se hizo este mantenimiento
                    estado_mant.append({
                        "Estado": "⚪",
                        "Mantenimiento": mant_tipo,
                        "Último Cambio": "Nunca registrado",
                        "Próximo": "Pendiente programar",
                        "Faltan": "-",
                        "Condición": "SIN REGISTRO"
                    })
            
            df_estado = pd.DataFrame(estado_mant)
            st.dataframe(
                df_estado,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Estado": st.column_config.TextColumn("", width="small"),
                    "Condición": st.column_config.TextColumn("Condición", width="small")
                }
            )
            
            # Historial completo
            with st.expander("📜 Ver Historial Completo de Mantenimientos"):
                st.dataframe(df_mant_hist, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No hay mantenimientos registrados para esta unidad.")
            st.info("💡 **Sugerencia:** Registra los mantenimientos realizados para activar el sistema preventivo.")
        
        st.divider()
        
        # ========================================
        # DOCUMENTACIÓN Y VENCIMIENTOS
        # ========================================
        st.subheader("📅 Documentación y Vencimientos")
        
        df_venc = pd.read_sql_query("""
            SELECT 
                tipo,
                fecha_vencimiento,
                fecha_ultimo,
                alerta_dias,
                observaciones
            FROM vencimientos
            WHERE vehiculo_id = ?
            ORDER BY fecha_vencimiento
        """, conn, params=(veh_id,))
        
        if not df_venc.empty:
            docs_estado = []
            for _, doc in df_venc.iterrows():
                dias = dias_hasta(doc['fecha_vencimiento'])
                
                if dias < 0:
                    icono = "🔴"
                    estado = "VENCIDO"
                elif dias < 7:
                    icono = "🟠"
                    estado = "URGENTE"
                elif dias < 30:
                    icono = "🟡"
                    estado = "PRÓXIMO"
                else:
                    icono = "🟢"
                    estado = "VIGENTE"
                
                docs_estado.append({
                    "": icono,
                    "Documento": doc['tipo'].upper(),
                    "Vencimiento": doc['fecha_vencimiento'],
                    "Días Restantes": f"{dias} días",
                    "Estado": estado,
                    "Observaciones": doc['observaciones'] or "-"
                })
            
            df_docs = pd.DataFrame(docs_estado)
            st.dataframe(df_docs, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No hay documentación registrada para esta unidad.")
        
        st.divider()
        
        # ========================================
        # HISTORIAL DE COMBUSTIBLE
        # ========================================
        st.subheader("⛽ Análisis de Consumo de Combustible")
        
        df_comb = pd.read_sql_query("""
            SELECT 
                fecha,
                km,
                litros,
                costo_total,
                rendimiento,
                tipo_combustible,
                estacion
            FROM combustible
            WHERE vehiculo_id = ?
            ORDER BY fecha DESC
            LIMIT 20
        """, conn, params=(veh_id,))
        
        if not df_comb.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            rend_prom = df_comb['rendimiento'].mean()
            rend_min = df_comb['rendimiento'].min()
            rend_max = df_comb['rendimiento'].max()
            costo_total = df_comb['costo_total'].sum()
            
            col1.metric("📊 Rendimiento Promedio", f"{rend_prom:.2f} km/l")
            col2.metric("⬇️ Mínimo", f"{rend_min:.2f} km/l")
            col3.metric("⬆️ Máximo", f"{rend_max:.2f} km/l")
            col4.metric("💰 Gasto Total", f"${costo_total:,.2f}")
            
            with st.expander("📊 Ver Últimas 20 Cargas"):
                st.dataframe(df_comb, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ No hay registros de combustible para esta unidad.")
        
        st.divider()
        
        # ========================================
        # HISTORIAL DE FALLAS
        # ========================================
        st.subheader("⚠️ Historial de Fallas y Reparaciones")
        
        df_fallas = pd.read_sql_query("""
            SELECT 
                fecha,
                tipo_falla,
                descripcion,
                gravedad,
                tiempo_inmovilizado_hrs,
                costo_reparacion,
                solucion
            FROM fallas
            WHERE vehiculo_id = ?
            ORDER BY fecha DESC
        """, conn, params=(veh_id,))
        
        if not df_fallas.empty:
            st.warning(f"⚠️ Esta unidad tiene **{len(df_fallas)} fallas registradas**.")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔴 Fallas Críticas", len(df_fallas[df_fallas['gravedad'] == 'critica']))
            col2.metric("⏱️ Horas Inmovilizado", f"{df_fallas['tiempo_inmovilizado_hrs'].sum():.0f} hrs")
            col3.metric("💸 Costo Reparaciones", f"${df_fallas['costo_reparacion'].sum():,.2f}")
            
            with st.expander("📋 Ver Detalle de Fallas"):
                st.dataframe(df_fallas, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Esta unidad no tiene fallas registradas. ¡Excelente!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    mostrar_ficha_unidad()