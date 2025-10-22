# reports/exporter.py
import pandas as pd
from utils.helpers import get_db_connection
from io import BytesIO

def exportar_flota_a_excel():
    conn = get_db_connection()
    
    # Cargar datos
    df_vehiculos = pd.read_sql_query("SELECT * FROM vehiculos", conn)
    df_vencimientos = pd.read_sql_query("""
        SELECT v.patente, ve.tipo, ve.fecha_vencimiento, ve.observaciones
        FROM vencimientos ve
        JOIN vehiculos v ON ve.vehiculo_id = v.id
    """, conn)
    df_mant = pd.read_sql_query("""
        SELECT v.patente, m.tipo, m.fecha, m.km, m.costo, m.taller
        FROM mantenimientos m
        JOIN vehiculos v ON m.vehiculo_id = v.id
    """, conn)

    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_vehiculos.to_excel(writer, sheet_name="Vehículos", index=False)
        df_vencimientos.to_excel(writer, sheet_name="Vencimientos", index=False)
        df_mant.to_excel(writer, sheet_name="Mantenimientos", index=False)
    
    return output.getvalue()