# views/gestion_vehiculos.py
import streamlit as st
import pandas as pd
from utils.helpers import get_db_connection

def gestion_vehiculos():
    st.header("🚛 Gestión de Vehículos")
    tab1, tab2, tab3 = st.tabs(["➕ Alta", "✏️ Edición", "🗑️ Baja Lógica"])

    # === ALTA ===
    with tab1:
        with st.form("alta_vehiculo"):
            st.subheader("Registrar Nuevo Vehículo")
            col1, col2, col3 = st.columns(3)
            patente = col1.text_input("Patente *", placeholder="Ej: ABC123").upper()
            tipo = col2.selectbox("Tipo *", ["camion", "camioneta", "auto", "utilitario"])
            marca = col3.text_input("Marca *")
            modelo = st.text_input("Modelo *")
            anio = st.number_input("Año", min_value=1980, max_value=2030, value=2020)
            chasis = st.text_input("Chasis")
            motor = st.text_input("Motor")
            centro = st.text_input("Centro Operativo")
            km = st.number_input("Kilometraje Inicial", min_value=0, value=0)
            obs = st.text_area("Observaciones")
            submitted = st.form_submit_button("💾 Registrar Vehículo", use_container_width=True)
            if submitted:
                if not patente or not marca or not modelo:
                    st.warning("⚠️ Complete los campos obligatorios (*)")
                else:
                    conn = get_db_connection()
                    try:
                        conn.execute("""
                            INSERT INTO vehiculos 
                            (patente, tipo, marca, modelo, anio, chasis, motor, centro_operativo, km_actual, observaciones)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (patente, tipo, marca, modelo, anio, chasis, motor, centro, km, obs))
                        conn.commit()
                        st.success(f"✅ Vehículo {patente} registrado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        conn.close()

    # === EDICIÓN ===
    with tab2:
        conn = get_db_connection()
        try:
            df = pd.read_sql_query("SELECT id, patente, marca, modelo, km_actual, estado FROM vehiculos ORDER BY patente", conn)
        finally:
            conn.close()
        if df.empty:
            st.info("ℹ️ No hay vehículos registrados")
            return
        patente_sel = st.selectbox("Seleccionar vehículo", df["patente"].tolist())
        veh = df[df["patente"] == patente_sel].iloc[0]
        conn = get_db_connection()
        try:
            datos = conn.execute("SELECT * FROM vehiculos WHERE id = ?", (veh["id"],)).fetchone()
        finally:
            conn.close()
        if datos:
            with st.form("editar_vehiculo"):
                st.subheader(f"Editar: {patente_sel}")
                col1, col2, col3 = st.columns(3)
                patente = col1.text_input("Patente", value=datos["patente"]).upper()
                tipo = col2.selectbox("Tipo", ["camion", "camioneta", "auto", "utilitario"], 
                                     index=["camion", "camioneta", "auto", "utilitario"].index(datos["tipo"]))
                marca = col3.text_input("Marca", value=datos["marca"])
                modelo = st.text_input("Modelo", value=datos["modelo"])
                anio = st.number_input("Año", min_value=1980, max_value=2030, value=datos["anio"] or 2020)
                chasis = st.text_input("Chasis", value=datos["chasis"] or "")
                motor = st.text_input("Motor", value=datos["motor"] or "")
                centro = st.text_input("Centro Operativo", value=datos["centro_operativo"] or "")
                km = st.number_input("Kilometraje Actual", min_value=0, value=datos["km_actual"] or 0)
                estado = st.selectbox("Estado", ["activo", "en_reparacion", "detenido", "baja"],
                                     index=["activo", "en_reparacion", "detenido", "baja"].index(datos["estado"]))
                obs = st.text_area("Observaciones", value=datos["observaciones"] or "")
                if st.form_submit_button("💾 Actualizar", use_container_width=True):
                    conn = get_db_connection()
                    try:
                        conn.execute("""
                            UPDATE vehiculos SET
                            patente=?, tipo=?, marca=?, modelo=?, anio=?, chasis=?, motor=?,
                            centro_operativo=?, km_actual=?, estado=?, observaciones=?
                            WHERE id=?
                        """, (patente, tipo, marca, modelo, anio, chasis, motor, centro, km, estado, obs, datos["id"]))
                        conn.commit()
                        st.success("✅ Vehículo actualizado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                    finally:
                        conn.close()

    # === BAJA LÓGICA ===
    with tab3:
        st.subheader("Dar de Baja un Vehículo")
        patente_baja = st.selectbox("Vehículo a dar de baja", df["patente"].tolist(), key="baja")
        if st.button("🗑️ Confirmar Baja", type="secondary", use_container_width=True):
            conn = get_db_connection()
            try:
                conn.execute("UPDATE vehiculos SET estado = 'baja' WHERE patente = ?", (patente_baja,))
                conn.commit()
                st.success(f"✅ Vehículo {patente_baja} dado de baja")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                conn.close()