# -*- coding: utf-8 -*-
# cargar_datos_demo.py - DATOS DE PRUEBA REALISTAS PARA DEMOSTRACIÓN

import sqlite3
from pathlib import Path
from datetime import date, timedelta
import random

DB_PATH = Path(__file__).parent / "data" / "flota.db"

def cargar_datos_demo():
    """Carga datos de prueba realistas para demostración"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🚀 Cargando datos de demostración...")
    
    # ==========================================
    # 1. VEHÍCULOS
    # ==========================================
    vehiculos = [
        ("AA123BB", "camion", "Scania", "R450", 2018, "CHASIS123", "MOTOR123", "Depósito Norte", 150000, "activo"),
        ("AB456CD", "camion", "Mercedes-Benz", "Actros 2041", 2019, "CHASIS456", "MOTOR456", "Depósito Sur", 120000, "activo"),
        ("AC789EF", "camion", "Volvo", "FH 460", 2020, "CHASIS789", "MOTOR789", "Depósito Norte", 95000, "activo"),
        ("AD012GH", "camioneta", "Ford", "Ranger XLT", 2021, "CHASIS012", "MOTOR012", "Administración", 45000, "activo"),
        ("AE345IJ", "camioneta", "Toyota", "Hilux SR", 2020, "CHASIS345", "MOTOR345", "Operaciones", 38000, "activo"),
        ("AF678KL", "camion", "Iveco", "Stralis 460", 2017, "CHASIS678", "MOTOR678", "Depósito Sur", 180000, "en_reparacion"),
        ("AG901MN", "auto", "Chevrolet", "Cruze", 2019, "CHASIS901", "MOTOR901", "Gerencia", 52000, "activo"),
        ("AH234OP", "camion", "Scania", "P320", 2016, "CHASIS234", "MOTOR234", "Depósito Norte", 220000, "activo"),
        ("AI567QR", "camioneta", "Nissan", "Frontier", 2022, "CHASIS567", "MOTOR567", "Operaciones", 28000, "activo"),
        ("AJ890ST", "camion", "Mercedes-Benz", "Atego 1726", 2018, "CHASIS890", "MOTOR890", "Depósito Sur", 165000, "detenido"),
    ]
    
    print("📦 Cargando vehículos...")
    for v in vehiculos:
        try:
            cursor.execute("""
                INSERT INTO vehiculos (patente, tipo, marca, modelo, anio, chasis, motor, 
                                     centro_operativo, km_actual, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, v)
        except sqlite3.IntegrityError:
            print(f"  ⚠️ Vehículo {v[0]} ya existe, saltando...")
    
    conn.commit()
    print(f"  ✅ {len(vehiculos)} vehículos cargados")
    
    # ==========================================
    # 2. CONDUCTORES
    # ==========================================
    conductores = [
        ("Juan Carlos Gómez", "20123456", "1985-03-15", "+54 381 5551234", "jgomez@empresa.com", "D2 - Más de 3500kg", 
         date.today() + timedelta(days=180), date.today() + timedelta(days=365), date.today() + timedelta(days=200), 
         date.today() + timedelta(days=400), 1, "activo"),
        ("María Elena Fernández", "27234567", "1990-07-22", "+54 381 5552345", "mfernandez@empresa.com", "D1 - Hasta 3500kg",
         date.today() + timedelta(days=90), None, date.today() + timedelta(days=150), None, 4, "activo"),
        ("Roberto Carlos Díaz", "18345678", "1980-11-10", "+54 381 5553456", "rdiaz@empresa.com", "D3 - Articulado/Semirremolque",
         date.today() - timedelta(days=15), date.today() + timedelta(days=300), date.today() + timedelta(days=100), 
         date.today() + timedelta(days=500), 2, "activo"),
        ("Ana Lucía Rojas", "29456789", "1992-05-18", "+54 381 5554567", "arojas@empresa.com", "Profesional",
         date.today() + timedelta(days=250), date.today() + timedelta(days=180), date.today() + timedelta(days=220), 
         date.today() + timedelta(days=350), 5, "activo"),
        ("Carlos Alberto Sánchez", "22567890", "1988-09-30", "+54 381 5555678", "csanchez@empresa.com", "E1 - Cargas Peligrosas",
         date.today() + timedelta(days=320), date.today() + timedelta(days=280), date.today() + timedelta(days=190), 
         date.today() + timedelta(days=450), 3, "activo"),
        ("Patricia Beatriz López", "25678901", "1987-12-05", "+54 381 5556789", "plopez@empresa.com", "D2 - Más de 3500kg",
         date.today() + timedelta(days=45), None, date.today() + timedelta(days=120), None, 8, "activo"),
        ("Jorge Luis Martínez", "19789012", "1983-04-20", "+54 381 5557890", "jmartinez@empresa.com", "D2 - Más de 3500kg",
         date.today() + timedelta(days=400), date.today() + timedelta(days=365), date.today() + timedelta(days=300), 
         date.today() + timedelta(days=600), 6, "activo"),
    ]
    
    print("👨‍✈️ Cargando conductores...")
    for c in conductores:
        try:
            cursor.execute("""
                INSERT INTO conductores (nombre, dni, fecha_nacimiento, telefono, email, licencia_tipo,
                                       licencia_venc, licencia_cargas_peligrosas, examen_psicofisico, 
                                       curso_iram, vehiculo_asignado, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, c)
        except sqlite3.IntegrityError:
            print(f"  ⚠️ Conductor {c[0]} ya existe, saltando...")
    
    conn.commit()
    print(f"  ✅ {len(conductores)} conductores cargados")
    
    # ==========================================
    # 3. MANTENIMIENTOS
    # ==========================================
    print("🔧 Cargando mantenimientos...")
    
    tipos_mantenimiento = [
        "Aceite de Motor",
        "Filtro de Aceite",
        "Filtro de Aire",
        "Filtro de Gasoil",
        "Filtro Separador de Agua",
        "Trampa de Agua",
        "Pastillas de Freno",
        "Aceite de Caja",
        "Aceite de Diferencial"
    ]
    
    intervales_km = {
        "Aceite de Motor": 10000,
        "Filtro de Aceite": 10000,
        "Filtro de Aire": 20000,
        "Filtro de Gasoil": 20000,
        "Filtro Separador de Agua": 15000,
        "Trampa de Agua": 10000,
        "Pastillas de Freno": 40000,
        "Aceite de Caja": 50000,
        "Aceite de Diferencial": 50000
    }
    
    talleres = ["Taller Scania Tucumán", "Mecánica del Norte", "Service Total", "Taller Mercedes-Benz"]
    
    # Cargar mantenimientos para cada vehículo
    for veh in vehiculos[:6]:  # Solo primeros 6 vehículos para demo
        patente, tipo, marca, modelo, anio, chasis, motor, centro, km_actual, estado = veh
        veh_id = cursor.execute("SELECT id FROM vehiculos WHERE patente=?", (patente,)).fetchone()[0]
        
        for tipo_mant in tipos_mantenimiento:
            intervalo = intervales_km[tipo_mant]
            
            # Calcular último mantenimiento
            km_ultimo = km_actual - random.randint(500, 5000)
            fecha_ultimo = date.today() - timedelta(days=random.randint(10, 120))
            
            # Calcular próximo
            km_prox = km_ultimo + intervalo
            fecha_prox = date.today() + timedelta(days=random.randint(30, 180))
            
            costo = random.uniform(5000, 50000)
            taller = random.choice(talleres)
            
            cursor.execute("""
                INSERT INTO mantenimientos 
                (vehiculo_id, tipo, categoria, fecha, km, costo, taller, 
                 prox_fecha, prox_km, alerta_km, observaciones)
                VALUES (?, ?, 'preventivo', ?, ?, ?, ?, ?, ?, 1000, 'Mantenimiento preventivo programado')
            """, (veh_id, tipo_mant, fecha_ultimo, km_ultimo, costo, taller, fecha_prox, km_prox))
    
    conn.commit()
    print(f"  ✅ Mantenimientos cargados para 6 vehículos")
    
    # ==========================================
    # 4. VENCIMIENTOS
    # ==========================================
    print("📅 Cargando vencimientos...")
    
    tipos_venc = ["VTV", "Seguro", "Patente", "Habilitación Municipal", "Transporte de Cargas Peligrosas"]
    
    for veh in vehiculos[:7]:  # Primeros 7 vehículos
        patente = veh[0]
        veh_id = cursor.execute("SELECT id FROM vehiculos WHERE patente=?", (patente,)).fetchone()[0]
        
        for tipo_venc in tipos_venc:
            # Crear algunos vencimientos próximos y otros OK
            dias_random = random.choice([15, 25, 45, 90, 180, 365])
            fecha_venc = date.today() + timedelta(days=dias_random)
            fecha_ultimo = fecha_venc - timedelta(days=365)
            
            alerta = 30 if tipo_venc in ["VTV", "Seguro"] else 15
            costo = random.uniform(10000, 80000) if tipo_venc in ["VTV", "Seguro"] else random.uniform(5000, 30000)
            
            cursor.execute("""
                INSERT INTO vencimientos 
                (vehiculo_id, tipo, fecha_vencimiento, fecha_ultimo, alerta_dias, costo_renovacion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (veh_id, tipo_venc, fecha_venc, fecha_ultimo, alerta, costo))
    
    conn.commit()
    print(f"  ✅ Vencimientos cargados")
    
    # ==========================================
    # 5. COMBUSTIBLE
    # ==========================================
    print("⛽ Cargando registros de combustible...")
    
    estaciones = ["YPF Ruta 9", "Shell Centro", "Petrobras Norte", "Axion San Miguel"]
    
    for veh in vehiculos[:6]:
        patente = veh[0]
        km_actual = veh[8]
        veh_id = cursor.execute("SELECT id FROM vehiculos WHERE patente=?", (patente,)).fetchone()[0]
        
        # Crear 10 cargas de combustible en los últimos 3 meses
        km_base = km_actual - 30000
        
        for i in range(10):
            dias_atras = 90 - (i * 9)
            fecha_carga = date.today() - timedelta(days=dias_atras)
            
            km_carga = km_base + (i * 3000)
            litros = random.uniform(150, 400)
            precio_litro = random.uniform(450, 550)
            costo_total = litros * precio_litro
            
            # Calcular rendimiento
            if i > 0:
                km_anteriores = cursor.execute("""
                    SELECT km FROM combustible 
                    WHERE vehiculo_id=? 
                    ORDER BY fecha DESC LIMIT 1
                """, (veh_id,)).fetchone()
                
                if km_anteriores:
                    km_recorridos = km_carga - km_anteriores[0]
                    rendimiento = km_recorridos / litros
                else:
                    rendimiento = random.uniform(2.0, 3.5)
            else:
                rendimiento = random.uniform(2.0, 3.5)
            
            estacion = random.choice(estaciones)
            
            cursor.execute("""
                INSERT INTO combustible 
                (vehiculo_id, fecha, km, litros, costo_total, precio_litro, 
                 tipo_combustible, estacion, rendimiento)
                VALUES (?, ?, ?, ?, ?, ?, 'diesel', ?, ?)
            """, (veh_id, fecha_carga, km_carga, litros, costo_total, precio_litro, estacion, rendimiento))
    
    conn.commit()
    print(f"  ✅ Registros de combustible cargados")
    
    # ==========================================
    # 6. FALLAS (algunas unidades)
    # ==========================================
    print("⚠️ Cargando historial de fallas...")
    
    tipos_falla = [
        "Falla en sistema de inyección",
        "Pérdida de potencia en motor",
        "Problemas en caja de cambios",
        "Fuga de aceite",
        "Problemas eléctricos",
        "Falla en turbo",
        "Sobrecalentamiento"
    ]
    
    # Solo 3 vehículos con fallas
    for veh in vehiculos[5:8]:  # Vehículos problemáticos
        patente = veh[0]
        veh_id = cursor.execute("SELECT id FROM vehiculos WHERE patente=?", (patente,)).fetchone()[0]
        
        # Crear 2-4 fallas
        num_fallas = random.randint(2, 4)
        
        for i in range(num_fallas):
            tipo_falla = random.choice(tipos_falla)
            fecha_falla = date.today() - timedelta(days=random.randint(10, 180))
            km_falla = random.randint(100000, 200000)
            gravedad = random.choice(["leve", "moderada", "grave"])
            tiempo_inmov = random.randint(2, 48)
            costo_rep = random.uniform(10000, 150000)
            
            descripcion = f"Falla detectada durante operación normal. {tipo_falla}"
            solucion = "Reparación en taller autorizado. Reemplazo de componentes necesarios."
            
            cursor.execute("""
                INSERT INTO fallas 
                (vehiculo_id, fecha, km, tipo_falla, descripcion, gravedad, 
                 tiempo_inmovilizado_hrs, costo_reparacion, solucion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (veh_id, fecha_falla, km_falla, tipo_falla, descripcion, gravedad, tiempo_inmov, costo_rep, solucion))
    
    conn.commit()
    print(f"  ✅ Historial de fallas cargado")
    
    # ==========================================
    # 7. NOTIFICACIONES
    # ==========================================
    print("📧 Cargando contactos para notificaciones...")
    
    contactos = [
        ("Gerente de Flota", "gerente.flota@empresa.com", "+54 381 4001000", "Gerente"),
        ("Jefe de Mantenimiento", "jefe.mantenimiento@empresa.com", "+54 381 4001001", "Jefe"),
        ("Encargado Operaciones", "operaciones@empresa.com", "+54 381 4001002", "Encargado"),
    ]
    
    for c in contactos:
        try:
            cursor.execute("""
                INSERT INTO notificaciones (nombre, email, telefono, cargo)
                VALUES (?, ?, ?, ?)
            """, c)
        except sqlite3.IntegrityError:
            print(f"  ⚠️ Contacto {c[0]} ya existe, saltando...")
    
    conn.commit()
    print(f"  ✅ Contactos para notificaciones cargados")
    
    # ==========================================
    # RESUMEN FINAL
    # ==========================================
    print("\n" + "="*60)
    print("✅ DATOS DE DEMOSTRACIÓN CARGADOS EXITOSAMENTE")
    print("="*60)
    
    # Estadísticas
    total_vehiculos = cursor.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0]
    total_conductores = cursor.execute("SELECT COUNT(*) FROM conductores").fetchone()[0]
    total_mantenimientos = cursor.execute("SELECT COUNT(*) FROM mantenimientos").fetchone()[0]
    total_vencimientos = cursor.execute("SELECT COUNT(*) FROM vencimientos").fetchone()[0]
    total_combustible = cursor.execute("SELECT COUNT(*) FROM combustible").fetchone()[0]
    total_fallas = cursor.execute("SELECT COUNT(*) FROM fallas").fetchone()[0]
    
    print(f"\n📊 RESUMEN:")
    print(f"   🚛 Vehículos: {total_vehiculos}")
    print(f"   👨‍✈️ Conductores: {total_conductores}")
    print(f"   🔧 Mantenimientos: {total_mantenimientos}")
    print(f"   📅 Vencimientos: {total_vencimientos}")
    print(f"   ⛽ Registros de combustible: {total_combustible}")
    print(f"   ⚠️ Fallas registradas: {total_fallas}")
    
    print(f"\n🎯 LISTO PARA DEMOSTRACIÓN:")
    print(f"   • Vehículos con historial completo")
    print(f"   • Alertas de mantenimiento pendientes")
    print(f"   • Documentación con vencimientos próximos")
    print(f"   • Análisis de rendimiento de combustible")
    print(f"   • Historial de fallas en algunas unidades")
    
    print("\n💡 EJECUTA: streamlit run app.py")
    print("="*60 + "\n")
    
    conn.close()


if __name__ == "__main__":
    cargar_datos_demo()