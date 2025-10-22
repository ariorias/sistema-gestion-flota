# -*- coding: utf-8 -*-
# models/__init__.py - ESTRUCTURA DE BASE DE DATOS
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "flota.db"

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    
    # Crear directorio si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # ===== TABLA: VEHÍCULOS =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patente TEXT UNIQUE NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('camion', 'camioneta', 'auto', 'utilitario')),
        marca TEXT,
        modelo TEXT,
        anio INTEGER,
        chasis TEXT,
        motor TEXT,
        estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'en_reparacion', 'detenido', 'baja')),
        centro_operativo TEXT,
        km_actual INTEGER DEFAULT 0,
        fecha_alta DATE DEFAULT CURRENT_DATE,
        observaciones TEXT
    )
    """)

    # ===== TABLA: CONDUCTORES =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conductores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        dni TEXT UNIQUE NOT NULL,
        fecha_nacimiento DATE,
        telefono TEXT,
        email TEXT,
        licencia_tipo TEXT,
        licencia_venc DATE,
        licencia_cargas_peligrosas DATE,
        examen_psicofisico DATE,
        curso_iram DATE,
        vehiculo_asignado INTEGER,
        estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'inactivo', 'suspendido')),
        observaciones TEXT,
        FOREIGN KEY(vehiculo_asignado) REFERENCES vehiculos(id) ON DELETE SET NULL
    )
    """)

    # ===== TABLA: VENCIMIENTOS =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vencimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehiculo_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        fecha_ultimo DATE,
        alerta_dias INTEGER DEFAULT 30,
        costo_renovacion REAL,
        observaciones TEXT,
        estado TEXT DEFAULT 'activo' CHECK(estado IN ('activo', 'renovado', 'vencido')),
        FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE
    )
    """)

    # ===== TABLA: MANTENIMIENTOS =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mantenimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehiculo_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        categoria TEXT CHECK(categoria IN ('preventivo', 'correctivo', 'emergencia')),
        fecha DATE NOT NULL,
        km INTEGER,
        costo REAL DEFAULT 0,
        taller TEXT,
        mecanico TEXT,
        prox_fecha DATE,
        prox_km INTEGER,
        alerta_km INTEGER DEFAULT 1000,
        observaciones TEXT,
        repuestos_usados TEXT,
        FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE
    )
    """)

    # ===== TABLA: COMBUSTIBLE =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combustible (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehiculo_id INTEGER NOT NULL,
        fecha DATE NOT NULL,
        km INTEGER NOT NULL,
        litros REAL NOT NULL,
        costo_total REAL NOT NULL,
        precio_litro REAL,
        tipo_combustible TEXT CHECK(tipo_combustible IN ('diesel', 'nafta', 'gnc')),
        estacion TEXT,
        conductor_id INTEGER,
        rendimiento REAL,
        observaciones TEXT,
        FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
        FOREIGN KEY(conductor_id) REFERENCES conductores(id) ON DELETE SET NULL
    )
    """)

    # ===== TABLA: NOTIFICACIONES =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notificaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        telefono TEXT,
        cargo TEXT,
        recibe_alertas_criticas BOOLEAN DEFAULT 1,
        recibe_reportes_semanales BOOLEAN DEFAULT 1,
        activo BOOLEAN DEFAULT 1
    )
    """)

    # ===== TABLA: HISTORIAL DE FALLAS =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fallas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehiculo_id INTEGER NOT NULL,
        fecha DATE NOT NULL,
        km INTEGER,
        tipo_falla TEXT NOT NULL,
        descripcion TEXT,
        gravedad TEXT CHECK(gravedad IN ('leve', 'moderada', 'grave', 'critica')),
        tiempo_inmovilizado_hrs INTEGER,
        costo_reparacion REAL,
        solucion TEXT,
        FOREIGN KEY(vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE
    )
    """)

    # ===== ÍNDICES PARA OPTIMIZACIÓN =====
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehiculos_estado ON vehiculos(estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vencimientos_fecha ON vencimientos(fecha_vencimiento)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mantenimientos_proximo ON mantenimientos(prox_fecha, prox_km)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_combustible_fecha ON combustible(fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fallas_vehiculo ON fallas(vehiculo_id)")

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada exitosamente con todas las tablas.")

if __name__ == "__main__":
    init_db()