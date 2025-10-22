# -*- coding: utf-8 -*-
# views/mantenimientos.py - MÓDULO DE MANTENIMIENTOS PREVENTIVOS

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from utils.helpers import get_db_connection

def modulo_mantenimientos():
    """Módulo completo de gestión de mantenimientos preventivos"""
    
    st.header("🔧 Gestión de Mantenimientos Preventivos")
    
    tab1, tab2, tab3 = st.tabs(["➕ Registrar Mantenimiento", "📋 Historial", "⚠️ Pendientes"])
    
    # ==========================================
    # TAB 1: REGISTRAR MANTENIMIENTO
    # ==========================================
    with tab1:
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("""
                SELECT id, patente, marca, modelo, km_actual 
                FROM vehiculos 
                WHERE estado = 'activo' 
                ORDER BY patente
            """, conn)
        finally:
            conn.close()
        
        if df_veh.empty:
            st.warning("⚠️ No hay vehículos activos")
            return
        
        vehiculos_dict = {f"{row['patente']} - {row['marca']} {row['modelo']} ({row['km_actual']:,} km)": 
                         (row['id'], row['km_actual']) 
                         for _, row in df_veh.iterrows()}
        
        with st.form("nuevo_mantenimiento"):
            st.subheader("📝 Registrar Mantenimiento Realizado")
            
            vehiculo_sel = st.selectbox("🚛 Vehículo", list(vehiculos_dict.keys()))
            veh_id, km_sugerido = vehiculos_dict[vehiculo_sel]
            
            col1, col2 = st.columns(2)
            
            tipo_mant = col1.selectbox("🔧 Tipo de Mantenimiento", [
                "Aceite de Motor",
                "Filtro de Aceite",
                "Filtro de Aire",
                "Filtro de Gasoil",
                "Filtro Separador de Agua",
                "Trampa de Agua",
                "Pastillas de Freno",
                "Discos de Freno",
                "Líquido de Frenos",
                "Aceite de Caja",
                "Aceite de Diferencial",
                "Batería",
                "Correa de Distribución",
                "Correa de Accesorios",
                "Bujías",
                "Neumáticos - Rotación",
                "Neumáticos - Cambio",
                "Alineación y Balanceo",
                "Luces y Balizas",
                "Matafuego - Recarga",
                "Otro"
            ])
            
            categoria = col2.selectbox("📂 Categoría", [
                "preventivo",
                "correctivo",
                "emergencia"
            ])
            
            col1, col2 = st.columns(2)
            fecha_mant = col1.date_input("📅 Fecha del Mantenimiento", value=date.today())
            km_actual = col2.number_input("🛣️ Kilometraje al momento", value=km_sugerido, min_value=0)
            
            st.subheader("💰 Costos y Detalles")
            
            col1, col2 = st.columns(2)
            costo = col1.number_input("💵 Costo Total (ARS)", min_value=0.0, step=100.0)
            taller = col2.text_input("🏪 Taller / Proveedor")
            
            mecanico = st.text_input("👨‍🔧 Mecánico Responsable")
            repuestos = st.text_area("📦 Repuestos Utilizados", 
                                     placeholder="Ej: Filtro Mann W719/5, Aceite Shell 15W40 x4L, etc.")
            
            st.subheader("📅 Programar Próximo Mantenimiento")
            
            col1, col2 = st.columns(2)
            
            # Intervalos predefinidos según tipo
            intervalos_km = {
                "Aceite de Motor": 10000,
                "Filtro de Aceite": 10000,
                "Filtro de Aire": 20000,
                "Filtro de Gasoil": 20000,
                "Filtro Separador de Agua": 15000,
                "Trampa de Agua": 10000,
                "Pastillas de Freno": 30000,
                "Aceite de Caja": 40000,
                "Aceite de Diferencial": 40000,
            }
            
            intervalo_sugerido = intervalos_km.get(tipo_mant, 10000)
            
            prox_km = col1.number_input(
                "🛣️ Próximo por KM",
                value=km_actual + intervalo_sugerido,
                help=f"Sugerido: cada {intervalo_sugerido:,} km"
            )
            
            alerta_km = col1.number_input(
                "🔔 Alertar con (km de anticipación)",
                value=1000,
                min_value=100,
                max_value=5000,
                step=100
            )
            
            prox_fecha = col2.date_input(
                "📅 Próxima fecha sugerida",
                value=date.today() + timedelta(days=180)
            )
            
            observaciones = st.text_area("📝 Observaciones Generales")
            
            submitted = st.form_submit_button("💾 Guardar Mantenimiento", use_container_width=True)
            
            if submitted:
                conn = get_db_connection()
                try:
                    # Actualizar kilometraje del vehículo
                    conn.execute("UPDATE vehiculos SET km_actual = ? WHERE id = ?", (km_actual, veh_id))
                    
                    # Insertar mantenimiento
                    conn.execute("""
                        INSERT INTO mantenimientos 
                        (vehiculo_id, tipo, categoria, fecha, km, costo, taller, mecanico,
                         prox_fecha, prox_km, alerta_km, observaciones, repuestos_usados)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (veh_id, tipo_mant, categoria, fecha_mant, km_actual, costo, taller, 
                         mecanico, prox_fecha, prox_km, alerta_km, observaciones, repuestos))
                    
                    conn.commit()
                    st.success(f"✅ Mantenimiento de {tipo_mant} registrado exitosamente")
                    st.success(f"✅ Kilometraje actualizado a {km_actual:,} km")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
    
    # ==========================================
    # TAB 2: HISTORIAL COMPLETO
    # ==========================================
    with tab2:
        st.subheader("📋 Historial de Mantenimientos")
        
        conn = get_db_connection()
        try:
            df_hist = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    m.fecha,
                    m.tipo,
                    m.categoria,
                    m.km,
                    m.costo,
                    m.taller,
                    m.prox_km,
                    m.prox_fecha,
                    m.observaciones
                FROM mantenimientos m
                JOIN vehiculos v ON m.vehiculo_id = v.id
                ORDER BY m.fecha DESC
                LIMIT 100
            """, conn)
            
            if not df_hist.empty:
                # Filtros
                col1, col2, col3, col4 = st.columns(4)
                
                patentes = ["Todas"] + sorted(df_hist['patente'].unique().tolist())
                filtro_patente = col1.selectbox("Filtrar por patente", patentes)
                
                tipos = ["Todos"] + sorted(df_hist['tipo'].unique().tolist())
                filtro_tipo = col2.selectbox("Filtrar por tipo", tipos)
                
                categorias = ["Todas"] + sorted(df_hist['categoria'].unique().tolist())
                filtro_cat = col3.selectbox("Filtrar por categoría", categorias)
                
                fecha_desde = col4.date_input("Desde", value=date.today() - timedelta(days=90))
                
                # Aplicar filtros
                df_filtrado = df_hist.copy()
                
                if filtro_patente != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['patente'] == filtro_patente]
                
                if filtro_tipo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['tipo'] == filtro_tipo]
                
                if filtro_cat != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_cat]
                
                df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['fecha']) >= pd.to_datetime(fecha_desde)]
                
                # Estadísticas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📊 Total Registros", len(df_filtrado))
                col2.metric("💰 Costo Total", f"${df_filtrado['costo'].sum():,.2f}")
                col3.metric("💵 Costo Promedio", f"${df_filtrado['costo'].mean():,.2f}")
                col4.metric("🔧 Talleres", df_filtrado['taller'].nunique())
                
                # Tabla
                st.dataframe(
                    df_filtrado[['patente', 'fecha', 'tipo', 'categoria', 'km', 'costo', 'taller']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "km": st.column_config.NumberColumn("KM", format="%d"),
                        "costo": st.column_config.NumberColumn("Costo", format="$ %.2f")
                    }
                )
                
            else:
                st.info("ℹ️ No hay mantenimientos registrados")
        
        finally:
            conn.close()
    
    # ==========================================
    # TAB 3: MANTENIMIENTOS PENDIENTES
    # ==========================================
    with tab3:
        st.subheader("⚠️ Mantenimientos Pendientes")
        
        conn = get_db_connection()
        try:
            # Por kilometraje
            df_km = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    v.km_actual,
                    m.tipo,
                    m.km as ultimo_km,
                    m.prox_km,
                    (m.prox_km - v.km_actual) as km_faltantes,
                    m.alerta_km
                FROM mantenimientos m
                JOIN vehiculos v ON m.vehiculo_id = v.id
                WHERE v.estado = 'activo'
                AND m.prox_km IS NOT NULL
                AND v.km_actual IS NOT NULL
                AND (m.prox_km - v.km_actual) <= m.alerta_km
                ORDER BY km_faltantes
            """, conn)
            
            # Por fecha
            df_fecha = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    m.tipo,
                    m.fecha as ultimo_mant,
                    m.prox_fecha,
                    julianday(m.prox_fecha) - julianday('now') as dias_faltantes
                FROM mantenimientos m
                JOIN vehiculos v ON m.vehiculo_id = v.id
                WHERE v.estado = 'activo'
                AND m.prox_fecha IS NOT NULL
                AND julianday(m.prox_fecha) - julianday('now') <= 30
                ORDER BY dias_faltantes
            """, conn)
            
            if not df_km.empty or not df_fecha.empty:
                total_pendientes = len(df_km) + len(df_fecha)
                st.warning(f"⚠️ **{total_pendientes} mantenimientos requieren atención**")
                
                # Pendientes por KM
                if not df_km.empty:
                    st.subheader("🛣️ Pendientes por Kilometraje")
                    
                    for _, row in df_km.iterrows():
                        km_falt = row['km_faltantes']
                        
                        if km_falt < 0:
                            color = "🔴"
                            estado = "VENCIDO"
                        elif km_falt < 500:
                            color = "🟠"
                            estado = "URGENTE"
                        else:
                            color = "🟡"
                            estado = "PRÓXIMO"
                        
                        st.markdown(f"{color} **{row['patente']}** - {row['tipo']} | "
                                  f"Actual: {row['km_actual']:,} km → Próximo: {row['prox_km']:,} km | "
                                  f"Faltan: {km_falt:,} km | **{estado}**")
                
                # Pendientes por Fecha
                if not df_fecha.empty:
                    st.subheader("📅 Pendientes por Fecha")
                    
                    for _, row in df_fecha.iterrows():
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
                        
                        st.markdown(f"{color} **{row['patente']}** - {row['tipo']} | "
                                  f"Próximo: {row['prox_fecha']} | "
                                  f"Faltan: {dias} días | **{estado}**")
            
            else:
                st.success("✅ ¡Excelente! Todos los mantenimientos están al día")
        
        finally:
            conn.close()


if __name__ == "__main__":
    modulo_mantenimientos()