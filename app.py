# -*- coding: utf-8 -*-
# app.py - SISTEMA INTEGRAL DE GESTIÓN DE FLOTA - VERSIÓN COMPLETA
import streamlit as st
import sqlite3
from datetime import date, datetime
import pandas as pd

# Importar módulos propios
from models import init_db
from utils.helpers import get_db_connection

# Inicializar base de datos
init_db()

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Gestión de Flota - Combustibles Tucumán",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚛"
)

# CSS Personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚛 Sistema Integral de Gestión de Flota</p>', unsafe_allow_html=True)
st.caption("✨ DESARROLLADO POR GUSTAVO SÁNCHEZ - TUCUMÁN, ARGENTINA")

# ==========================================
# MENÚ DE NAVEGACIÓN
# ==========================================
menu = st.sidebar.radio("📋 Menú Principal", [
    "🏠 Dashboard",
    "🚗 Vehículos (ABM)",
    "👨‍✈️ Conductores (ABM)",
    "📋 Historial por Unidad",
    "📅 Vencimientos",
    "🔧 Mantenimientos",
    "⛽ Combustible",
    "📊 Análisis Avanzado",
    "🔍 Ficha de Unidad",
    "👤 Ficha de Conductor",
    "🔔 Alertas por Email",
    "📄 Reportes"
])

# ==========================================
# 🏠 DASHBOARD PRINCIPAL
# ==========================================
if menu == "🏠 Dashboard":
    st.header("📊 Centro de Control de Flota")
    
    conn = get_db_connection()
    
    try:
        # KPIs principales
        total = conn.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0]
        activos = conn.execute("SELECT COUNT(*) FROM vehiculos WHERE estado = 'activo'").fetchone()[0]
        reparacion = conn.execute("SELECT COUNT(*) FROM vehiculos WHERE estado = 'en_reparacion'").fetchone()[0]
        detenidos = conn.execute("SELECT COUNT(*) FROM vehiculos WHERE estado = 'detenido'").fetchone()[0]
        
        # Cumplimiento
        vencidos = conn.execute("""
            SELECT COUNT(*) FROM vencimientos v
            JOIN vehiculos ve ON v.vehiculo_id = ve.id
            WHERE ve.estado != 'baja' AND v.fecha_vencimiento < date('now')
        """).fetchone()[0]
        
        total_docs = conn.execute("""
            SELECT COUNT(*) FROM vencimientos v
            JOIN vehiculos ve ON v.vehiculo_id = ve.id
            WHERE ve.estado != 'baja'
        """).fetchone()[0]
        
        cumplimiento = 100 if total_docs == 0 else round((total_docs - vencidos) / total_docs * 100, 1)
        
        # Mostrar KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🚛 Total Unidades", total)
        col2.metric("✅ Operativas", activos, delta=f"{reparacion} en taller")
        col3.metric("🛑 Detenidas", detenidos)
        col4.metric("📌 Cumplimiento", f"{cumplimiento}%")
        
        st.divider()
        
        # Alertas críticas
        st.subheader("🚨 Alertas Críticas - Próximos 30 Días")
        
        df_alertas = pd.read_sql_query("""
            SELECT 
                v.patente,
                'Vencimiento' as tipo,
                ve.tipo as item,
                ve.fecha_vencimiento as fecha,
                julianday(ve.fecha_vencimiento) - julianday('now') as dias
            FROM vencimientos ve
            JOIN vehiculos v ON ve.vehiculo_id = v.id
            WHERE v.estado = 'activo' 
            AND julianday(ve.fecha_vencimiento) - julianday('now') <= 30
            
            UNION ALL
            
            SELECT 
                v.patente,
                'Mantenimiento' as tipo,
                m.tipo as item,
                m.prox_fecha as fecha,
                julianday(m.prox_fecha) - julianday('now') as dias
            FROM mantenimientos m
            JOIN vehiculos v ON m.vehiculo_id = v.id
            WHERE v.estado = 'activo' 
            AND m.prox_fecha IS NOT NULL
            AND julianday(m.prox_fecha) - julianday('now') <= 30
            
            ORDER BY dias
        """, conn)
        
        if not df_alertas.empty:
            # Agregar estado
            df_alertas['Estado'] = df_alertas['dias'].apply(
                lambda x: "🔴 VENCIDO" if x < 0 else "🟠 URGENTE" if x < 7 else "🟡 PRÓXIMO"
            )
            df_alertas['Días'] = df_alertas['dias'].apply(lambda x: f"{int(x)} días")
            
            st.dataframe(
                df_alertas[['Estado', 'patente', 'tipo', 'item', 'fecha', 'Días']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No hay alertas críticas en los próximos 30 días")
    
    finally:
        conn.close()

# ==========================================
# 🚗 VEHÍCULOS (ABM)
# ==========================================
elif menu == "🚗 Vehículos (ABM)":
    from views.abm_vehiculos import abm_vehiculos
    abm_vehiculos()

# ==========================================
# 👨‍✈️ CONDUCTORES (ABM)
# ==========================================
elif menu == "👨‍✈️ Conductores (ABM)":
    from views.abm_conductores import abm_conductores
    abm_conductores()

# ==========================================
# 📋 HISTORIAL POR UNIDAD
# ==========================================
elif menu == "📋 Historial por Unidad":
    from views.historial_unidad import vista_historial_unidad
    vista_historial_unidad()

# ==========================================
# 📅 VENCIMIENTOS
# ==========================================
elif menu == "📅 Vencimientos":
    from views.vencimientos import modulo_vencimientos
    modulo_vencimientos()

# ==========================================
# 🔧 MANTENIMIENTOS
# ==========================================
elif menu == "🔧 Mantenimientos":
    from views.mantenimientos import modulo_mantenimientos
    modulo_mantenimientos()

# ==========================================
# ⛽ COMBUSTIBLE
# ==========================================
elif menu == "⛽ Combustible":
    from views.combustible import modulo_combustible
    modulo_combustible()

# ==========================================
# 📊 ANÁLISIS AVANZADO
# ==========================================
elif menu == "📊 Análisis Avanzado":
    from views.dashboard_avanzado import mostrar_dashboard_avanzado
    mostrar_dashboard_avanzado()

# ==========================================
# 🔍 FICHA DE UNIDAD
# ==========================================
elif menu == "🔍 Ficha de Unidad":
    from views.unidad_detalle import mostrar_ficha_unidad
    mostrar_ficha_unidad()

# ==========================================
# 👤 FICHA DE CONDUCTOR
# ==========================================
elif menu == "👤 Ficha de Conductor":
    from views.conductor_detalle import mostrar_ficha_conductor
    mostrar_ficha_conductor()

# ==========================================
# 🔔 ALERTAS POR EMAIL
# ==========================================
elif menu == "🔔 Alertas por Email":
    from services.email_alerts import SistemaAlertas, obtener_destinatarios_activos
    
    st.header("🔔 Sistema de Alertas Automáticas por Email")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuración", "📧 Enviar Ahora", "📋 Destinatarios"])
    
    with tab1:
        st.subheader("⚙️ Configuración del Sistema de Emails")
        
        with st.form("config_email"):
            st.info("📧 Configura las credenciales de Gmail para envío automático")
            
            email_from = st.text_input("Email de envío (Gmail)", placeholder="tu_email@gmail.com")
            password = st.text_input("Contraseña de aplicación", type="password", 
                                    help="Genera una contraseña de aplicación en tu cuenta de Google")
            
            st.caption("💡 **Nota:** Debes habilitar 'Contraseñas de aplicaciones' en tu cuenta de Gmail")
            
            submitted = st.form_submit_button("💾 Guardar Configuración")
            
            if submitted and email_from and password:
                st.session_state['email_from'] = email_from
                st.session_state['email_password'] = password
                st.success("✅ Configuración guardada exitosamente")
    
    with tab2:
        st.subheader("📧 Enviar Alertas Ahora")
        
        if 'email_from' not in st.session_state:
            st.warning("⚠️ Primero configura las credenciales de email en la pestaña 'Configuración'")
        else:
            destinatarios = obtener_destinatarios_activos()
            
            if destinatarios:
                st.info(f"📬 Se enviará a: {', '.join(destinatarios)}")
                
                if st.button("📤 Enviar Alertas por Email", use_container_width=True):
                    with st.spinner("Enviando..."):
                        sistema = SistemaAlertas()
                        sistema.configurar_email(
                            st.session_state['email_from'],
                            st.session_state['email_password']
                        )
                        
                        exito, mensaje = sistema.enviar_alerta_email(destinatarios)
                        
                        if exito:
                            st.success(mensaje)
                        else:
                            st.error(mensaje)
            else:
                st.warning("⚠️ No hay destinatarios activos. Agrega contactos en la pestaña 'Destinatarios'")
    
    with tab3:
        st.subheader("📋 Gestión de Destinatarios")
        
        with st.form("nuevo_destinatario"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre")
            email = col2.text_input("Email")
            
            col1, col2 = st.columns(2)
            telefono = col1.text_input("Teléfono (opcional)")
            cargo = col2.text_input("Cargo (opcional)")
            
            submitted = st.form_submit_button("➕ Agregar Destinatario")
            
            if submitted and nombre and email:
                conn = get_db_connection()
                try:
                    conn.execute("""
                        INSERT INTO notificaciones (nombre, email, telefono, cargo)
                        VALUES (?, ?, ?, ?)
                    """, (nombre, email, telefono, cargo))
                    conn.commit()
                    st.success("✅ Destinatario agregado")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ El email ya está registrado")
                finally:
                    conn.close()
        
        # Listado
        conn = get_db_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM notificaciones WHERE activo = 1", conn)
            if not df.empty:
                st.dataframe(df[['nombre', 'email', 'telefono', 'cargo']], 
                           use_container_width=True, hide_index=True)
        finally:
            conn.close()

# ==========================================
# 📄 REPORTES
# ==========================================
elif menu == "📄 Reportes":
    from reports.exporter import exportar_flota_a_excel
    
    st.header("📄 Exportar Reportes")
    st.write("Descarga toda la información de la flota en formato Excel.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Reporte Completo", use_container_width=True):
            excel_data = exportar_flota_a_excel()
            st.download_button(
                label="⬇️ Descargar Excel",
                data=excel_data,
                file_name=f"reporte_flota_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📊 Reporte de Mantenimientos", use_container_width=True):
            conn = get_db_connection()
            try:
                df = pd.read_sql_query("""
                    SELECT 
                        v.patente,
                        m.tipo,
                        m.fecha,
                        m.km,
                        m.costo,
                        m.taller,
                        m.prox_km,
                        m.prox_fecha
                    FROM mantenimientos m
                    JOIN vehiculos v ON m.vehiculo_id = v.id
                    ORDER BY m.fecha DESC
                """, conn)
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Convertir a CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"mantenimientos_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            finally:
                conn.close()
    
    with col3:
        if st.button("⛽ Reporte de Combustible", use_container_width=True):
            conn = get_db_connection()
            try:
                df = pd.read_sql_query("""
                    SELECT 
                        v.patente,
                        c.fecha,
                        c.km,
                        c.litros,
                        c.costo_total,
                        c.rendimiento,
                        c.estacion
                    FROM combustible c
                    JOIN vehiculos v ON c.vehiculo_id = v.id
                    ORDER BY c.fecha DESC
                """, conn)
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"combustible_{date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            finally:
                conn.close()

# ==========================================
# FOOTER
# ==========================================
st.sidebar.markdown("---")
st.sidebar.caption("💡 Sistema desarrollado por Gustavo Sánchez")
st.sidebar.caption("📍 San Miguel de Tucumán, Argentina")
st.sidebar.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")