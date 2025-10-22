# -*- coding: utf-8 -*-
# views/abm_conductores.py - ABM COMPLETO DE CONDUCTORES

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
from utils.helpers import get_db_connection, dias_hasta

def abm_conductores():
    """ABM completo de conductores con gestión de documentación"""
    
    st.header("👨‍✈️ Administración de Conductores")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Alta", "✏️ Modificación", "🗑️ Baja", "📋 Listado", "📄 Vista Documentación"])
    
    # ==========================================
    # TAB 1: ALTA DE CONDUCTOR
    # ==========================================
    with tab1:
        st.subheader("➕ Registrar Nuevo Conductor")
        
        # Obtener vehículos disponibles
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("""
                SELECT id, patente FROM vehiculos 
                WHERE estado = 'activo'
                ORDER BY patente
            """, conn)
        finally:
            conn.close()
        
        vehiculos_dict = {"(Sin asignar)": None}
        vehiculos_dict.update({row['patente']: row['id'] for _, row in df_veh.iterrows()})
        
        with st.form("alta_conductor", clear_on_submit=True):
            st.markdown("### 📝 Datos Personales")
            
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Completo *", placeholder="Juan Pérez")
            dni = col2.text_input("DNI *", placeholder="12345678")
            
            col1, col2, col3 = st.columns(3)
            fecha_nac = col1.date_input("Fecha de Nacimiento", value=None)
            telefono = col2.text_input("Teléfono", placeholder="+54 381 1234567")
            email = col3.text_input("Email", placeholder="conductor@empresa.com")
            
            domicilio = st.text_input("Domicilio", placeholder="Calle 123, San Miguel de Tucumán")
            
            st.markdown("### 🪪 Documentación Obligatoria")
            
            col1, col2 = st.columns(2)
            
            # Licencia de conducir
            lic_tipo = col1.selectbox("Tipo de Licencia *", [
                "Profesional",
                "D1 - Hasta 3500kg",
                "D2 - Más de 3500kg",
                "D3 - Articulado/Semirremolque",
                "E1 - Cargas Peligrosas",
                "Particular"
            ])
            
            lic_venc = col2.date_input(
                "Vencimiento Licencia *",
                value=date.today() + timedelta(days=365)
            )
            
            col1, col2 = st.columns(2)
            
            # Habilitación cargas peligrosas
            tiene_cargas = col1.checkbox("¿Tiene habilitación de cargas peligrosas?")
            if tiene_cargas:
                cargas_venc = col2.date_input(
                    "Vencimiento Cargas Peligrosas",
                    value=date.today() + timedelta(days=365)
                )
            else:
                cargas_venc = None
            
            st.markdown("### 🏥 Documentación Sanitaria")
            
            col1, col2 = st.columns(2)
            
            tiene_psicofisico = col1.checkbox("¿Tiene examen psicofísico?")
            if tiene_psicofisico:
                psico_venc = col2.date_input(
                    "Vencimiento Psicofísico",
                    value=date.today() + timedelta(days=365)
                )
            else:
                psico_venc = None
            
            col1, col2 = st.columns(2)
            
            tiene_iram = col1.checkbox("¿Tiene curso IRAM?")
            if tiene_iram:
                iram_venc = col2.date_input(
                    "Vencimiento Curso IRAM",
                    value=date.today() + timedelta(days=730)
                )
            else:
                iram_venc = None
            
            st.markdown("### 🚛 Asignación de Vehículo")
            
            vehiculo_asig = st.selectbox("Vehículo Asignado", list(vehiculos_dict.keys()))
            
            observaciones = st.text_area("📝 Observaciones")
            
            submitted = st.form_submit_button("💾 Registrar Conductor", use_container_width=True)
            
            if submitted and nombre and dni:
                veh_id = vehiculos_dict[vehiculo_asig]
                
                conn = get_db_connection()
                try:
                    conn.execute("""
                        INSERT INTO conductores 
                        (nombre, dni, fecha_nacimiento, telefono, email, licencia_tipo, 
                         licencia_venc, licencia_cargas_peligrosas, examen_psicofisico, 
                         curso_iram, vehiculo_asignado, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nombre, dni, fecha_nac, telefono, email, lic_tipo, lic_venc,
                         cargas_venc, psico_venc, iram_venc, veh_id, observaciones))
                    
                    conn.commit()
                    st.success(f"✅ Conductor **{nombre}** registrado exitosamente")
                    st.balloons()
                    
                except sqlite3.IntegrityError:
                    st.error("❌ Error: El DNI ya existe en el sistema")
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
        st.subheader("✏️ Modificar Conductor Existente")
        
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
            st.info("ℹ️ No hay conductores registrados")
            return
        
        # Selector de conductor
        conductor_sel = st.selectbox(
            "Seleccione el conductor a modificar",
            df_cond['nombre'].tolist(),
            format_func=lambda x: f"{x} - DNI: {df_cond[df_cond['nombre']==x]['dni'].iloc[0]}"
        )
        
        cond_data = df_cond[df_cond['nombre'] == conductor_sel].iloc[0]
        
        # Obtener vehículos
        conn = get_db_connection()
        try:
            df_veh = pd.read_sql_query("SELECT id, patente FROM vehiculos WHERE estado = 'activo'", conn)
        finally:
            conn.close()
        
        vehiculos_dict = {"(Sin asignar)": None}
        vehiculos_dict.update({row['patente']: row['id'] for _, row in df_veh.iterrows()})
        
        # Determinar vehículo actual
        veh_actual = cond_data['patente'] if cond_data['patente'] else "(Sin asignar)"
        
        with st.form("modificar_conductor"):
            st.markdown(f"### Editando: **{cond_data['nombre']}**")
            
            col1, col2 = st.columns(2)
            nuevo_nombre = col1.text_input("Nombre Completo", value=cond_data['nombre'])
            nuevo_dni = col2.text_input("DNI", value=cond_data['dni'])
            
            col1, col2, col3 = st.columns(3)
            nueva_fecha_nac = col1.date_input("Fecha Nacimiento", value=pd.to_datetime(cond_data['fecha_nacimiento']) if cond_data['fecha_nacimiento'] else None)
            nuevo_telefono = col2.text_input("Teléfono", value=cond_data['telefono'] or "")
            nuevo_email = col3.text_input("Email", value=cond_data['email'] or "")
            
            st.markdown("### 🪪 Documentación")
            
            col1, col2 = st.columns(2)
            nuevo_lic_tipo = col1.selectbox("Tipo Licencia", 
                ["Profesional", "D1 - Hasta 3500kg", "D2 - Más de 3500kg", "D3 - Articulado/Semirremolque", "E1 - Cargas Peligrosas", "Particular"],
                index=0 if not cond_data['licencia_tipo'] else 0)
            nueva_lic_venc = col2.date_input("Venc. Licencia", value=pd.to_datetime(cond_data['licencia_venc']))
            
            col1, col2 = st.columns(2)
            nueva_cargas = col1.date_input("Cargas Peligrosas", value=pd.to_datetime(cond_data['licencia_cargas_peligrosas']) if cond_data['licencia_cargas_peligrosas'] else None)
            nuevo_psico = col2.date_input("Psicofísico", value=pd.to_datetime(cond_data['examen_psicofisico']) if cond_data['examen_psicofisico'] else None)
            
            nuevo_iram = st.date_input("Curso IRAM", value=pd.to_datetime(cond_data['curso_iram']) if cond_data['curso_iram'] else None)
            
            nuevo_veh = st.selectbox("Vehículo Asignado", list(vehiculos_dict.keys()),
                                    index=list(vehiculos_dict.keys()).index(veh_actual) if veh_actual in vehiculos_dict else 0)
            
            nuevo_estado = st.selectbox("Estado", ["activo", "inactivo", "suspendido"],
                                       index=["activo", "inactivo", "suspendido"].index(cond_data['estado']))
            
            nuevas_obs = st.text_area("Observaciones", value=cond_data['observaciones'] or "")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submitted:
                nuevo_veh_id = vehiculos_dict[nuevo_veh]
                
                conn = get_db_connection()
                try:
                    conn.execute("""
                        UPDATE conductores 
                        SET nombre=?, dni=?, fecha_nacimiento=?, telefono=?, email=?,
                            licencia_tipo=?, licencia_venc=?, licencia_cargas_peligrosas=?,
                            examen_psicofisico=?, curso_iram=?, vehiculo_asignado=?, 
                            estado=?, observaciones=?
                        WHERE id=?
                    """, (nuevo_nombre, nuevo_dni, nueva_fecha_nac, nuevo_telefono, nuevo_email,
                         nuevo_lic_tipo, nueva_lic_venc, nueva_cargas, nuevo_psico, nuevo_iram,
                         nuevo_veh_id, nuevo_estado, nuevas_obs, cond_data['id']))
                    
                    conn.commit()
                    st.success(f"✅ Conductor **{nuevo_nombre}** actualizado correctamente")
                    st.rerun()
                    
                except sqlite3.IntegrityError:
                    st.error("❌ Error: El DNI ya existe")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
    
    # ==========================================
    # TAB 3: BAJA
    # ==========================================
    with tab3:
        st.subheader("🗑️ Dar de Baja Conductor")
        
        st.warning("⚠️ **ATENCIÓN:** Dar de baja un conductor cambiará su estado a 'inactivo'.")
        
        conn = get_db_connection()
        try:
            df_activos = pd.read_sql_query("""
                SELECT id, nombre, dni
                FROM conductores 
                WHERE estado = 'activo'
                ORDER BY nombre
            """, conn)
        finally:
            conn.close()
        
        if df_activos.empty:
            st.info("ℹ️ No hay conductores activos")
            return
        
        conductor_baja = st.selectbox(
            "Seleccione el conductor a dar de baja",
            df_activos['nombre'].tolist(),
            format_func=lambda x: f"{x} - DNI: {df_activos[df_activos['nombre']==x]['dni'].iloc[0]}"
        )
        
        cond_baja_data = df_activos[df_activos['nombre'] == conductor_baja].iloc[0]
        
        st.metric("Conductor", cond_baja_data['nombre'])
        st.metric("DNI", cond_baja_data['dni'])
        
        motivo_baja = st.text_area("Motivo de la baja *", placeholder="Ej: Renuncia, despido, fin de contrato, etc.")
        
        confirmar = st.checkbox("⚠️ Confirmo que deseo dar de baja este conductor")
        
        if st.button("🗑️ CONFIRMAR BAJA", type="primary", disabled=not confirmar):
            if motivo_baja:
                conn = get_db_connection()
                try:
                    conn.execute("""
                        UPDATE conductores 
                        SET estado='inactivo', observaciones=?, vehiculo_asignado=NULL
                        WHERE id=?
                    """, (f"BAJA: {motivo_baja}", cond_baja_data['id']))
                    
                    conn.commit()
                    st.success(f"✅ Conductor **{cond_baja_data['nombre']}** dado de baja correctamente")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Debe especificar el motivo de la baja")
    
    # ==========================================
    # TAB 4: LISTADO
    # ==========================================
    with tab4:
        st.subheader("📋 Listado Completo de Conductores")
        
        conn = get_db_connection()
        try:
            df_todos = pd.read_sql_query("""
                SELECT 
                    c.nombre,
                    c.dni,
                    c.telefono,
                    c.licencia_tipo,
                    c.licencia_venc,
                    c.estado,
                    v.patente as vehiculo
                FROM conductores c
                LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.id
                ORDER BY 
                    CASE c.estado
                        WHEN 'activo' THEN 1
                        WHEN 'suspendido' THEN 2
                        WHEN 'inactivo' THEN 3
                    END,
                    c.nombre
            """, conn)
            
            if not df_todos.empty:
                # Filtros
                col1, col2 = st.columns(2)
                
                estados_filtro = ["Todos"] + sorted(df_todos['estado'].unique().tolist())
                filtro_estado = col1.selectbox("Filtrar por estado", estados_filtro)
                
                # Aplicar filtros
                df_filtrado = df_todos.copy()
                
                if filtro_estado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
                
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                col1.metric("Total", len(df_filtrado))
                col2.metric("Activos", len(df_filtrado[df_filtrado['estado'] == 'activo']))
                col3.metric("Inactivos", len(df_filtrado[df_filtrado['estado'] == 'inactivo']))
                
                # Tabla
                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.info("ℹ️ No hay conductores registrados")
        
        finally:
            conn.close()
    
    # ==========================================
    # TAB 5: VISTA DOCUMENTACIÓN
    # ==========================================
    with tab5:
        st.subheader("📄 Estado de Documentación por Conductor")
        
        conn = get_db_connection()
        try:
            df_docs = pd.read_sql_query("""
                SELECT 
                    nombre,
                    dni,
                    licencia_venc,
                    licencia_cargas_peligrosas,
                    examen_psicofisico,
                    curso_iram,
                    estado
                FROM conductores
                WHERE estado = 'activo'
                ORDER BY nombre
            """, conn)
            
            if not df_docs.empty:
                # Crear tabla de estado de documentación
                datos_tabla = []
                
                for _, cond in df_docs.iterrows():
                    # Licencia
                    if cond['licencia_venc']:
                        dias_lic = dias_hasta(cond['licencia_venc'])
                        estado_lic = "🔴" if dias_lic < 0 else "🟠" if dias_lic < 15 else "🟢"
                    else:
                        estado_lic = "⚪"
                        dias_lic = None
                    
                    # Cargas peligrosas
                    if cond['licencia_cargas_peligrosas']:
                        dias_cargas = dias_hasta(cond['licencia_cargas_peligrosas'])
                        estado_cargas = "🔴" if dias_cargas < 0 else "🟠" if dias_cargas < 15 else "🟢"
                    else:
                        estado_cargas = "⚪"
                        dias_cargas = None
                    
                    # Psicofísico
                    if cond['examen_psicofisico']:
                        dias_psico = dias_hasta(cond['examen_psicofisico'])
                        estado_psico = "🔴" if dias_psico < 0 else "🟠" if dias_psico < 15 else "🟢"
                    else:
                        estado_psico = "⚪"
                        dias_psico = None
                    
                    # IRAM
                    if cond['curso_iram']:
                        dias_iram = dias_hasta(cond['curso_iram'])
                        estado_iram = "🔴" if dias_iram < 0 else "🟠" if dias_iram < 15 else "🟢"
                    else:
                        estado_iram = "⚪"
                        dias_iram = None
                    
                    datos_tabla.append({
                        "Conductor": cond['nombre'],
                        "DNI": cond['dni'],
                        "Licencia": f"{estado_lic} {cond['licencia_venc']}",
                        "Días": dias_lic if dias_lic is not None else "-",
                        "Cargas Pel.": f"{estado_cargas} {cond['licencia_cargas_peligrosas'] or 'N/A'}",
                        "Días_2": dias_cargas if dias_cargas is not None else "-",
                        "Psicofísico": f"{estado_psico} {cond['examen_psicofisico'] or 'N/A'}",
                        "Días_3": dias_psico if dias_psico is not None else "-",
                        "IRAM": f"{estado_iram} {cond['curso_iram'] or 'N/A'}",
                        "Días_4": dias_iram if dias_iram is not None else "-"
                    })
                
                df_vista = pd.DataFrame(datos_tabla)
                
                st.dataframe(
                    df_vista,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Alertas
                vencidos = []
                for _, cond in df_docs.iterrows():
                    docs_vencidos = []
                    
                    if cond['licencia_venc'] and dias_hasta(cond['licencia_venc']) < 0:
                        docs_vencidos.append("Licencia")
                    if cond['licencia_cargas_peligrosas'] and dias_hasta(cond['licencia_cargas_peligrosas']) < 0:
                        docs_vencidos.append("Cargas Peligrosas")
                    if cond['examen_psicofisico'] and dias_hasta(cond['examen_psicofisico']) < 0:
                        docs_vencidos.append("Psicofísico")
                    if cond['curso_iram'] and dias_hasta(cond['curso_iram']) < 0:
                        docs_vencidos.append("IRAM")
                    
                    if docs_vencidos:
                        vencidos.append(f"**{cond['nombre']}**: {', '.join(docs_vencidos)}")
                
                if vencidos:
                    st.error("🚨 **CONDUCTORES CON DOCUMENTACIÓN VENCIDA:**")
                    for v in vencidos:
                        st.markdown(f"- {v}")
                else:
                    st.success("✅ Todos los conductores tienen su documentación al día")
                
            else:
                st.info("ℹ️ No hay conductores activos")
        
        finally:
            conn.close()


if __name__ == "__main__":
    abm_conductores()