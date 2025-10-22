# utils/helpers.py
from datetime import datetime, date
from pathlib import Path
import sqlite3
DB_PATH = Path(__file__).parent.parent / "data" / "flota.db"
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def dias_hasta(fecha_str):
    if not fecha_str:
        return 999
    try:
        hoy = date.today()
        venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        return (venc - hoy).days
    except (ValueError, TypeError):
        return 999