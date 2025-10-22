# -*- coding: utf-8 -*-
# services/email_alerts.py - SISTEMA DE ALERTAS AUTOMÁTICAS

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
from utils.helpers import get_db_connection, dias_hasta
import pandas as pd

class SistemaAlertas:
    """Sistema de envío automático de alertas por email"""
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = None
        self.email_password = None
    
    def configurar_email(self, email_from, password):
        """Configura las credenciales del email"""
        self.email_from = email_from
        self.email_password = password
    
    def obtener_alertas_criticas(self):
        """Obtiene todas las alertas críticas del sistema"""
        conn = get_db_connection()
        alertas = {
            "vehiculos_vencidos": [],
            "mantenimientos_urgentes": [],
            "conductores_vencidos": [],
            "vehiculos_detenidos": []
        }
        
        try:
            # 1. DOCUMENTACIÓN DE VEHÍCULOS VENCIDA O PRÓXIMA
            df_venc = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    ve.tipo,
                    ve.fecha_vencimiento,
                    julianday(ve.fecha_vencimiento) - julianday('now') as dias_faltantes
                FROM vencimientos ve
                JOIN vehiculos v ON ve.vehiculo_id = v.id
                WHERE v.estado = 'activo'
                AND julianday(ve.fecha_vencimiento) - julianday('now') <= 30
                ORDER BY dias_faltantes
            """, conn)
            
            for _, row in df_venc.iterrows():
                dias = int(row['dias_faltantes'])
                prioridad = "CRÍTICO" if dias < 0 else "URGENTE" if dias < 7 else "ADVERTENCIA"
                
                alertas["vehiculos_vencidos"].append({
                    "patente": row['patente'],
                    "tipo": row['tipo'],
                    "vencimiento": row['fecha_vencimiento'],
                    "dias": dias,
                    "prioridad": prioridad
                })
            
            # 2. MANTENIMIENTOS PRÓXIMOS POR KM
            df_mant_km = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    v.km_actual,
                    m.tipo,
                    m.prox_km,
                    (m.prox_km - v.km_actual) as km_faltantes
                FROM mantenimientos m
                JOIN vehiculos v ON m.vehiculo_id = v.id
                WHERE v.estado = 'activo'
                AND m.prox_km IS NOT NULL
                AND v.km_actual IS NOT NULL
                AND (m.prox_km - v.km_actual) <= 2000
                ORDER BY km_faltantes
            """, conn)
            
            for _, row in df_mant_km.iterrows():
                km = row['km_faltantes']
                prioridad = "CRÍTICO" if km < 0 else "URGENTE" if km < 500 else "ADVERTENCIA"
                
                alertas["mantenimientos_urgentes"].append({
                    "patente": row['patente'],
                    "tipo": row['tipo'],
                    "km_actual": row['km_actual'],
                    "proximo": row['prox_km'],
                    "faltantes": km,
                    "prioridad": prioridad
                })
            
            # 3. MANTENIMIENTOS PRÓXIMOS POR FECHA
            df_mant_fecha = pd.read_sql_query("""
                SELECT 
                    v.patente,
                    m.tipo,
                    m.prox_fecha,
                    julianday(m.prox_fecha) - julianday('now') as dias_faltantes
                FROM mantenimientos m
                JOIN vehiculos v ON m.vehiculo_id = v.id
                WHERE v.estado = 'activo'
                AND m.prox_fecha IS NOT NULL
                AND julianday(m.prox_fecha) - julianday('now') <= 30
                ORDER BY dias_faltantes
            """, conn)
            
            for _, row in df_mant_fecha.iterrows():
                dias = int(row['dias_faltantes'])
                prioridad = "CRÍTICO" if dias < 0 else "URGENTE" if dias < 7 else "ADVERTENCIA"
                
                alertas["mantenimientos_urgentes"].append({
                    "patente": row['patente'],
                    "tipo": row['tipo'],
                    "fecha": row['prox_fecha'],
                    "dias": dias,
                    "prioridad": prioridad
                })
            
            # 4. CONDUCTORES CON DOCUMENTACIÓN VENCIDA
            df_cond = pd.read_sql_query("""
                SELECT 
                    nombre,
                    dni,
                    licencia_venc,
                    licencia_cargas_peligrosas,
                    examen_psicofisico,
                    curso_iram
                FROM conductores
                WHERE estado = 'activo'
            """, conn)
            
            for _, cond in df_cond.iterrows():
                docs_vencidos = []
                
                # Verificar cada documento
                if cond['licencia_venc']:
                    dias = dias_hasta(cond['licencia_venc'])
                    if dias <= 30:
                        docs_vencidos.append(("Licencia", cond['licencia_venc'], dias))
                
                if cond['licencia_cargas_peligrosas']:
                    dias = dias_hasta(cond['licencia_cargas_peligrosas'])
                    if dias <= 30:
                        docs_vencidos.append(("Cargas Peligrosas", cond['licencia_cargas_peligrosas'], dias))
                
                if cond['examen_psicofisico']:
                    dias = dias_hasta(cond['examen_psicofisico'])
                    if dias <= 30:
                        docs_vencidos.append(("Examen Psicofísico", cond['examen_psicofisico'], dias))
                
                if cond['curso_iram']:
                    dias = dias_hasta(cond['curso_iram'])
                    if dias <= 30:
                        docs_vencidos.append(("Curso IRAM", cond['curso_iram'], dias))
                
                if docs_vencidos:
                    for doc_tipo, fecha, dias in docs_vencidos:
                        prioridad = "CRÍTICO" if dias < 0 else "URGENTE" if dias < 7 else "ADVERTENCIA"
                        alertas["conductores_vencidos"].append({
                            "nombre": cond['nombre'],
                            "dni": cond['dni'],
                            "documento": doc_tipo,
                            "vencimiento": fecha,
                            "dias": dias,
                            "prioridad": prioridad
                        })
            
            # 5. VEHÍCULOS DETENIDOS O EN REPARACIÓN
            df_detenidos = pd.read_sql_query("""
                SELECT patente, estado, observaciones
                FROM vehiculos
                WHERE estado IN ('detenido', 'en_reparacion')
            """, conn)
            
            for _, veh in df_detenidos.iterrows():
                alertas["vehiculos_detenidos"].append({
                    "patente": veh['patente'],
                    "estado": veh['estado'],
                    "observaciones": veh['observaciones']
                })
        
        finally:
            conn.close()
        
        return alertas
    
    def generar_html_email(self, alertas, tipo="diario"):
        """Genera el HTML del email de alertas"""
        
        total_alertas = (
            len(alertas["vehiculos_vencidos"]) +
            len(alertas["mantenimientos_urgentes"]) +
            len(alertas["conductores_vencidos"]) +
            len(alertas["vehiculos_detenidos"])
        )
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .alert-section {{
                    margin-bottom: 25px;
                    border-left: 4px solid #667eea;
                    padding-left: 15px;
                }}
                .alert-section h2 {{
                    color: #333;
                    font-size: 20px;
                    margin-bottom: 15px;
                }}
                .alert-item {{
                    background-color: #f9f9f9;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                    border-left: 3px solid #ccc;
                }}
                .alert-critico {{
                    border-left-color: #ff4444;
                    background-color: #ffebee;
                }}
                .alert-urgente {{
                    border-left-color: #ffaa00;
                    background-color: #fff8e1;
                }}
                .alert-advertencia {{
                    border-left-color: #ffdd00;
                    background-color: #fffde7;
                }}
                .badge {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: bold;
                    margin-right: 5px;
                }}
                .badge-critico {{ background-color: #ff4444; color: white; }}
                .badge-urgente {{ background-color: #ffaa00; color: white; }}
                .badge-advertencia {{ background-color: #ffdd00; color: #333; }}
                .resumen {{
                    background-color: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 25px;
                    text-align: center;
                }}
                .resumen h3 {{
                    margin: 0;
                    color: #1976d2;
                    font-size: 18px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚛 Sistema de Gestión de Flota</h1>
                    <p>Reporte de Alertas - {date.today().strftime('%d/%m/%Y')}</p>
                </div>
                
                <div class="resumen">
                    <h3>📊 Total de Alertas: {total_alertas}</h3>
                </div>
        """
        
        # VEHÍCULOS CON DOCUMENTACIÓN VENCIDA
        if alertas["vehiculos_vencidos"]:
            html += """
                <div class="alert-section">
                    <h2>📅 Documentación de Vehículos</h2>
            """
            for alerta in alertas["vehiculos_vencidos"]:
                clase = f"alert-{alerta['prioridad'].lower()}"
                badge_clase = f"badge-{alerta['prioridad'].lower()}"
                estado_texto = "VENCIDO" if alerta['dias'] < 0 else f"Vence en {alerta['dias']} días"
                
                html += f"""
                    <div class="alert-item {clase}">
                        <span class="badge {badge_clase}">{alerta['prioridad']}</span>
                        <strong>{alerta['patente']}</strong> - {alerta['tipo'].upper()}<br>
                        <small>Vencimiento: {alerta['vencimiento']} | {estado_texto}</small>
                    </div>
                """
            html += "</div>"
        
        # MANTENIMIENTOS URGENTES
        if alertas["mantenimientos_urgentes"]:
            html += """
                <div class="alert-section">
                    <h2>🔧 Mantenimientos Preventivos</h2>
            """
            for alerta in alertas["mantenimientos_urgentes"]:
                clase = f"alert-{alerta['prioridad'].lower()}"
                badge_clase = f"badge-{alerta['prioridad'].lower()}"
                
                if 'faltantes' in alerta:  # Por kilometraje
                    estado = f"Faltan {alerta['faltantes']:,} km" if alerta['faltantes'] > 0 else "VENCIDO POR KM"
                    detalle = f"Actual: {alerta['km_actual']:,} km | Próximo: {alerta['proximo']:,} km"
                else:  # Por fecha
                    estado = f"Faltan {alerta['dias']} días" if alerta['dias'] > 0 else "VENCIDO POR FECHA"
                    detalle = f"Fecha programada: {alerta['fecha']}"
                
                html += f"""
                    <div class="alert-item {clase}">
                        <span class="badge {badge_clase}">{alerta['prioridad']}</span>
                        <strong>{alerta['patente']}</strong> - {alerta['tipo']}<br>
                        <small>{detalle} | {estado}</small>
                    </div>
                """
            html += "</div>"
        
        # CONDUCTORES CON DOCUMENTACIÓN VENCIDA
        if alertas["conductores_vencidos"]:
            html += """
                <div class="alert-section">
                    <h2>👨‍✈️ Documentación de Conductores</h2>
            """
            for alerta in alertas["conductores_vencidos"]:
                clase = f"alert-{alerta['prioridad'].lower()}"
                badge_clase = f"badge-{alerta['prioridad'].lower()}"
                estado = "VENCIDO" if alerta['dias'] < 0 else f"Vence en {alerta['dias']} días"
                
                html += f"""
                    <div class="alert-item {clase}">
                        <span class="badge {badge_clase}">{alerta['prioridad']}</span>
                        <strong>{alerta['nombre']}</strong> (DNI: {alerta['dni']})<br>
                        <small>{alerta['documento']} | Vencimiento: {alerta['vencimiento']} | {estado}</small>
                    </div>
                """
            html += "</div>"
        
        # VEHÍCULOS DETENIDOS
        if alertas["vehiculos_detenidos"]:
            html += """
                <div class="alert-section">
                    <h2>🛑 Vehículos Fuera de Servicio</h2>
            """
            for veh in alertas["vehiculos_detenidos"]:
                estado_txt = "EN REPARACIÓN" if veh['estado'] == 'en_reparacion' else "DETENIDO"
                html += f"""
                    <div class="alert-item alert-advertencia">
                        <span class="badge badge-advertencia">INFO</span>
                        <strong>{veh['patente']}</strong> - {estado_txt}<br>
                        <small>{veh['observaciones'] or 'Sin observaciones'}</small>
                    </div>
                """
            html += "</div>"
        
        # Si no hay alertas
        if total_alertas == 0:
            html += """
                <div style="text-align: center; padding: 40px;">
                    <h2 style="color: #4caf50;">✅ ¡Excelente!</h2>
                    <p>No hay alertas críticas en este momento. Toda la flota está operativa y con documentación al día.</p>
                </div>
            """
        
        html += """
                <div class="footer">
                    <p><strong>Sistema Integral de Gestión de Flota</strong></p>
                    <p>Combustibles Tucumán - Argentina</p>
                    <p>Este es un email automático, por favor no responder.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def enviar_alerta_email(self, destinatarios, asunto=None):
        """Envía el email de alertas a los destinatarios"""
        
        if not self.email_from or not self.email_password:
            raise ValueError("❌ Debe configurar las credenciales de email primero.")
        
        alertas = self.obtener_alertas_criticas()
        total_alertas = (
            len(alertas["vehiculos_vencidos"]) +
            len(alertas["mantenimientos_urgentes"]) +
            len(alertas["conductores_vencidos"]) +
            len(alertas["vehiculos_detenidos"])
        )
        
        if asunto is None:
            if total_alertas == 0:
                asunto = f"✅ Flota OK - {date.today().strftime('%d/%m/%Y')}"
            else:
                asunto = f"🚨 {total_alertas} Alertas de Flota - {date.today().strftime('%d/%m/%Y')}"
        
        html_content = self.generar_html_email(alertas)
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = asunto
        msg['From'] = self.email_from
        msg['To'] = ", ".join(destinatarios)
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        try:
            # Conectar y enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True, f"✅ Email enviado exitosamente a {len(destinatarios)} destinatarios."
        
        except Exception as e:
            return False, f"❌ Error al enviar email: {str(e)}"
    
    def programar_envio_automatico(self, hora="08:00", dias_semana=[0,1,2,3,4]):
        """
        Programa envío automático de alertas
        hora: Hora en formato "HH:MM"
        dias_semana: Lista de días (0=Lunes, 6=Domingo)
        """
        # Esta función requeriría un scheduler como APScheduler
        # Por ahora solo devuelve la configuración
        return {
            "hora": hora,
            "dias": dias_semana,
            "estado": "Configurado (requiere scheduler activo)"
        }


# Función helper para usar en Streamlit
def obtener_destinatarios_activos():
    """Obtiene la lista de emails activos de la base de datos"""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT email, nombre 
            FROM notificaciones 
            WHERE activo = 1 AND recibe_alertas_criticas = 1
        """, conn)
        return df['email'].tolist()
    finally:
        conn.close()


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del sistema
    sistema = SistemaAlertas()
    
    # Configurar credenciales (en producción, usar variables de entorno)
    sistema.configurar_email("tu_email@gmail.com", "tu_contraseña_app")
    
    # Obtener y mostrar alertas
    alertas = sistema.obtener_alertas_criticas()
    print(f"Total alertas: {sum(len(v) for v in alertas.values())}")
    
    # Enviar email (descomentar para probar)
    # destinatarios = ["responsable@empresa.com"]
    # exito, mensaje = sistema.enviar_alerta_email(destinatarios)
    # print(mensaje)