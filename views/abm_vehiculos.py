# -*- coding: utf-8 -*-
# views/abm_vehiculos.py - ABM COMPLETO DE VEHÍCULOS

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from utils.helpers import get_db_connection

def abm_vehiculos():
    """ABM completo de vehículos con plantillas de mantenimiento"""
    
    st.header("🚗 Administración de Vehículos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Alta", "✏️ Modificación", "🗑️ Baja", "📋 Listado Completo"])
    
    # ==========================================
    # TAB 1: ALTA DE VEHÍCULO
    # ==========================================
    with tab1:
        st.subheader("➕ Registrar Nuevo Vehículo")
        
        with st.form("alta_vehiculo", clear_on_submit=True):
            st.markdown("### 📝 Datos Básicos")
            
            col1, col2, col3 = st.columns(3)
            patente = col1.text_input("Patente *", placeholder="AA001BB").upper().replace(" ", "")
            tipo = col2.selectbox("Tipo de Vehículo *", [
                "camion",
                "camioneta", 
                "auto",
                "utilitario"
            ])
            marca = col3.text_input("Marca *", placeholder="Scania, Ford, etc.")
            
            col1, col2, col3 = st.columns(3)
            modelo = col1.text_input("Modelo *", placeholder="R450, Ranger, etc.")
            anio = col2.number_input("Año *", min_value=1980, max_value=2030, value=2020)
            centro = col3.text_input("Centro Operativo", placeholder="Depósito Norte")
            
            col1, col2 = st.columns(2)
            chasis = col1.text_input("Nº Chasis", placeholder="Opcional")
            motor = col2.text_input("Nº Motor", placeholder="Opcional")
            
            km_actual = st.number_input("Kilometraje Actual *", min_value=0, value=0, step=1000)
            
            st.markdown("### 🔧 Plantilla de Mantenimiento Inicial")
            st.info("💡 Configura los intervalos de mantenimiento según las especificaciones del fabricante")
            
            # Plantillas predefinidas según tipo de vehículo
            if tipo == "camion":
                intervalos_default = {
                    "Aceite de Motor": 10000,
                    "Filtro de Aceite": 10000,
                    "Filtro de Aire": 20000,
                    "Filtro de Gasoil": 20000,
                    "Filtro Separador de Agua": 15000,
                    "Trampa de Agua": 10000,
                    "Pastillas de Freno": 40000,
                    "Aceite de Caja": 50000,
                    "Aceite de Diferencial": 50000,
                }
            elif tipo == "camioneta":
                intervalos_default = {
                    "Aceite de Motor": 10000,
                    "Filtro de Aceite": 10000,
                    "Filtro de Aire": 15000,
                    "Filtro de Combustible": 20000,
                    "Pastillas de Freno": 30000,
                    "Aceite de Caja": 40000,
                }
            else:
                intervalos_default = {
                    "Aceite de Motor": 10000,
                    "Filtro de Aceite": 10000,
                    "Filtro de Aire": 15000,
                    "Pastillas de Freno": 25000,
                }
            
            usar_plantilla = st.checkbox("✅ Usar plantilla de mantenimiento recomendada", value=True)
            
            if usar_plantilla:
                st.markdown("**Intervalos configurados (km):**")
                cols = st.columns(3)
                for idx, (item, km) in enumerate(intervalos_default.items()):
                    cols[idx % 3].write(f"• {item}: {km:,} km")
            
            observaciones = st.text_area("📝 Observaciones")
            
            submitted = st.form_submit_button("💾 Registrar Vehículo", use_container_width=True)
            
            if submitted and patente and marca and modelo:
                conn = get_db_connection()
                try:
                    # Insertar vehículo
                    conn.execute("""
                        INSERT INTO vehiculos (patente, tipo, marca, modelo, anio, chasis, motor, 
                                             centro_operativo, km_actual, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (patente, tipo, marca, modelo, anio, chasis, motor, centro, km_actual, observaciones))
                    
                    veh_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    
                    # Si usa plantilla, crear mantenimientos iniciales
                    if usar_plantilla:
                        for item, intervalo in intervalos_default.items():
                            conn.execute("""
                                INSERT INTO mantenimientos 
                                (vehiculo_id, tipo, categoria, fecha, km, prox_km, alerta_km, observaciones)
                                VALUES (?, ?, 'preventivo', ?, ?, ?, 1000, 'Mantenimiento inicial')
                            """, (veh_id, item, date.today(), km_actual, km_actual + intervalo))
                    
                    conn.commit()
                    st.success(f"✅ Vehículo **{patente}** registrado exitosamente")
                    
                    if usar_plantilla:
                        st.success(f"✅ {len(intervalos_default)} plantillas de mantenimiento configuradas")
                    
                    st.balloons()
                    
                except sqlite3.IntegrityError:
                    st.error("❌ Error: La patente ya existe en el sistema")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
            
            elif submitted:
                st.warning("⚠️ Complete todos los campos obligatorios (*)")
    
    # ==========================================
    # TAB 2: MODIFICACIÓN
    # ==========================================
    with tab2:
        st.subheader("✏️ Modificar Vehículo Existente")
        
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("""
                SELECT id, patente, marca, modelo, tipo, anio, chasis, motor, 
                       centro_operativo, km_actual, estado, observaciones
                FROM vehiculos 
                ORDER BY patente
            """, conn)
        finally:
            conn.close()
        
        if df_veh.empty:
            st.info("ℹ️ No hay vehículos registrados")
            return
        
        # Selector de vehículo
        vehiculo_sel = st.selectbox(
            "Seleccione el vehículo a modificar",
            df_veh['patente'].tolist(),
            format_func=lambda x: f"{x} - {df_veh[df_veh['patente']==x]['marca'].iloc[0]} {df_veh[df_veh['patente']==x]['modelo'].iloc[0]}"
        )
        
        veh_data = df_veh[df_veh['patente'] == vehiculo_sel].iloc[0]
        
        with st.form("modificar_vehiculo"):
            st.markdown(f"### Editando: **{veh_data['patente']}**")
            
            col1, col2, col3 = st.columns(3)
            
            nueva_patente = col1.text_input("Patente", value=veh_data['patente']).upper()
            nuevo_tipo = col2.selectbox("Tipo", ["camion", "camioneta", "auto", "utilitario"], 
                                       index=["camion", "camioneta", "auto", "utilitario"].index(veh_data['tipo']))
            nueva_marca = col3.text_input("Marca", value=veh_data['marca'])
            
            col1, col2, col3 = st.columns(3)
            nuevo_modelo = col1.text_input("Modelo", value=veh_data['modelo'])
            nuevo_anio = col2.number_input("Año", min_value=1980, max_value=2030, value=int(veh_data['anio']))
            nuevo_centro = col3.text_input("Centro Operativo", value=veh_data['centro_operativo'] or "")
            
            col1, col2 = st.columns(2)
            nuevo_chasis = col1.text_input("Nº Chasis", value=veh_data['chasis'] or "")
            nuevo_motor = col2.text_input("Nº Motor", value=veh_data['motor'] or "")
            
            col1, col2 = st.columns(2)
            nuevo_km = col1.number_input("Kilometraje Actual", min_value=0, value=int(veh_data['km_actual']))
            nuevo_estado = col2.selectbox("Estado", ["activo", "en_reparacion", "detenido", "baja"],
                                         index=["activo", "en_reparacion", "detenido", "baja"].index(veh_data['estado']))
            
            nuevas_obs = st.text_area("Observaciones", value=veh_data['observaciones'] or "")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submitted:
                conn = get_db_connection()
                try:
                    conn.execute("""
                        UPDATE vehiculos 
                        SET patente=?, tipo=?, marca=?, modelo=?, anio=?, chasis=?, motor=?,
                            centro_operativo=?, km_actual=?, estado=?, observaciones=?
                        WHERE id=?
                    """, (nueva_patente, nuevo_tipo, nueva_marca, nuevo_modelo, nuevo_anio, 
                         nuevo_chasis, nuevo_motor, nuevo_centro, nuevo_km, nuevo_estado, 
                         nuevas_obs, veh_data['id']))
                    
                    conn.commit()
                    st.success(f"✅ Vehículo **{nueva_patente}** actualizado correctamente")
                    st.rerun()
                    
                except sqlite3.IntegrityError:
                    st.error("❌ Error: La patente ya existe")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
    
    # ==========================================
    # TAB 3: BAJA
    # ==========================================
    with tab3:
        st.subheader("🗑️ Dar de Baja Vehículo")
        
        st.warning("⚠️ **ATENCIÓN:** Dar de baja un vehículo cambiará su estado pero NO eliminará su historial.")
        
        conn = get_db_connection()
        try:
            df_activos = pd.read_sql_query("""
                SELECT id, patente, marca, modelo, tipo, km_actual
                FROM vehiculos 
                WHERE estado != 'baja'
                ORDER BY patente
            """, conn)
        finally:
            conn.close()
        
        if df_activos.empty:
            st.info("ℹ️ No hay vehículos activos")
            return
        
        vehiculo_baja = st.selectbox(
            "Seleccione el vehículo a dar de baja",
            df_activos['patente'].tolist(),
            format_func=lambda x: f"{x} - {df_activos[df_activos['patente']==x]['marca'].iloc[0]} {df_activos[df_activos['patente']==x]['modelo'].iloc[0]}"
        )
        
        veh_baja_data = df_activos[df_activos['patente'] == vehiculo_baja].iloc[0]
        
        col1, col2 = st.columns(2)
        col1.metric("Patente", veh_baja_data['patente'])
        col2.metric("Kilometraje", f"{veh_baja_data['km_actual']:,} km")
        
        motivo_baja = st.text_area("Motivo de la baja *", placeholder="Ej: Venta, siniestro total, fin de vida útil, etc.")
        
        confirmar = st.checkbox("⚠️ Confirmo que deseo dar de baja este vehículo")
        
        if st.button("🗑️ CONFIRMAR BAJA", type="primary", disabled=not confirmar):
            if motivo_baja:
                conn = get_db_connection()
                try:
                    conn.execute("""
                        UPDATE vehiculos 
                        SET estado='baja', observaciones=?
                        WHERE id=?
                    """, (f"BAJA: {motivo_baja}", veh_baja_data['id']))
                    
                    conn.commit()
                    st.success(f"✅ Vehículo **{veh_baja_data['patente']}** dado de baja correctamente")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Debe especificar el motivo de la baja")
    
    # ==========================================
    # TAB 4: LISTADO COMPLETO
    # ==========================================
    with tab4:
        st.subheader("📋 Listado Completo de Vehículos")
        
        conn = get_db_connection()
        try:
            df_todos = pd.read_sql_query("""
                SELECT patente, tipo, marca, modelo, anio, estado, km_actual, 
                       centro_operativo, fecha_alta
                FROM vehiculos 
                ORDER BY 
                    CASE estado
                        WHEN 'activo' THEN 1
                        WHEN 'en_reparacion' THEN 2
                        WHEN 'detenido' THEN 3
                        WHEN 'baja' THEN 4
                    END,
                    patente
            """, conn)
            
            if not df_todos.empty:
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                tipos_filtro = ["Todos"] + sorted(df_todos['tipo'].unique().tolist())
                filtro_tipo = col1.selectbox("Filtrar por tipo", tipos_filtro)
                
                estados_filtro = ["Todos"] + sorted(df_todos['estado'].unique().tolist())
                filtro_estado = col2.selectbox("Filtrar por estado", estados_filtro)
                
                # Aplicar filtros
                df_filtrado = df_todos.copy()
                
                if filtro_tipo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['tipo'] == filtro_tipo]
                
                if filtro_estado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
                
                # Estadísticas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total", len(df_filtrado))
                col2.metric("Activos", len(df_filtrado[df_filtrado['estado'] == 'activo']))
                col3.metric("En Reparación", len(df_filtrado[df_filtrado['estado'] == 'en_reparacion']))
                col4.metric("Detenidos", len(df_filtrado[df_filtrado['estado'] == 'detenido']))
                
                # Tabla con colores por estado
                def color_estado(val):
                    colors = {
                        'activo': 'background-color: #d4edda',
                        'en_reparacion': 'background-color: #fff3cd',
                        'detenido': 'background-color: #f8d7da',
                        'baja': 'background-color: #e2e3e5'
                    }
                    return colors.get(val, '')
                
                st.dataframe(
                    df_filtrado.style.applymap(color_estado, subset=['estado']),
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.info("ℹ️ No hay vehículos registrados")
        
        finally:
            conn.close()


if __name__ == "__main__":
    abm_vehiculos()