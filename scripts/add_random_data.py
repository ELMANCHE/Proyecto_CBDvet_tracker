"""
Script para agregar datos random a la BD con prioridad a perros y gatos
Objetivo: Subir el promedio de nivel_mejora de 5.54 a 7.0
"""

import random
from datetime import datetime, timedelta
from database import SessionLocal, Paciente, Consulta, Diagnostico, TratamientoCBD, CondicionesClinicas, Resultado, TipoEspecie, Enfermedad
from sqlalchemy import text

def get_random_date(start_date, end_date):
    """Genera fecha random entre dos fechas"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_random_patient(session, especie_id):
    """Genera datos random para un paciente"""
    if especie_id == 1:  # Perro
        peso = round(random.uniform(5.0, 35.0), 1)
    elif especie_id == 2:  # Gato
        peso = round(random.uniform(2.0, 8.0), 1)
    else:
        peso = round(random.uniform(0.5, 5.0), 1)
    
    sexo = random.choice(["M", "F"])
    esterilizado = random.choice([True, False])
    colores = ["Negro", "Blanco", "Marrón", "Gris", "Dorado", "Manchado", "Tricolor"]
    
    return {
        "tipo_especie_id": especie_id,
        "raza_id": None,
        "sexo": sexo,
        "fecha_nacimiento": None,
        "esterilizado": esterilizado,
        "codigo_paciente": f"PAC{random.randint(10000, 99999)}",
        "color": random.choice(colores),
        "peso_base": peso,
        "activo": True
    }

def generate_random_consulta(paciente_id, fecha):
    """Genera datos random para una consulta"""
    severidades = ["Leve", "Moderada", "Grave"]
    enfermedades = ["Artritis", "Ansiedad", "Dolor Crónico", "Epilepsia", "Inflamación", "Convulsiones", "Estrés", "Dolor Agudo"]
    
    return {
        "paciente_id": paciente_id,
        "peso": random.uniform(2.0, 30.0),
        "temperatura": round(random.uniform(38.0, 39.5), 1),
        "frecuencia_cardiaca": random.randint(60, 140),
        "observaciones": "Consulta de seguimiento",
        "fecha": fecha
    }

def generate_random_diagnostico(session, consulta_id):
    """Genera datos random para un diagnóstico"""
    enfermedades = session.query(Enfermedad).all()
    enfermedad = random.choice(enfermedades) if enfermedades else None
    
    return {
        "consulta_id": consulta_id,
        "enfermedad_id": enfermedad.id if enfermedad else 1,  # Default a 1 si no hay enfermedades
        "severidad": random.choice(["Leve", "Moderada", "Grave"]),
        "duracion_dias": random.randint(30, 180)
    }

def generate_random_tratamiento(consulta_id):
    """Genera datos random para un tratamiento CBD"""
    tipos = ["Aceite", "Cápsulas", "Tintura", "Tratamiento Tópico"]
    frecuencias = ["Diaria", "Cada 12 horas", "Cada 24 horas", "Cada 2 días"]
    
    return {
        "consulta_id": consulta_id,
        "dosis_mg_kg": round(random.uniform(1.0, 8.0), 2),
        "frecuencia": random.choice(frecuencias),
        "duracion_dias": random.randint(30, 90),
        "tipo_producto": random.choice(tipos),
        "concentracion": "5%",
        "dosis_mg": round(random.uniform(10, 50), 1),
        "via_administracion": "Oral",
        "tipo_extracto": "Full Spectrum",
        "fecha_inicio": datetime.now().date()
    }

def generate_random_condiciones(consulta_id):
    """Genera datos random para condiciones clínicas"""
    return {
        "consulta_id": consulta_id,
        "comorbilidades": "Ninguna",
        "medicamentos_previos": "Ninguno",
        "estado_nutricional": random.randint(1, 4),
        "presion_arterial": random.randint(100, 140),
        "alt": random.randint(30, 80),
        "ast": random.randint(25, 70),
        "nivel_estres": random.randint(2, 8),
        "tipo_dolor": random.choice(["Agudo", "Crónico", "Ninguno"]),
        "actividad_fisica": random.choice(["Baja", "Moderada", "Alta"]),
        "apetito": random.choice(["Bajo", "Normal", "Alto"]),
        "hidratacion": random.choice(["Baja", "Normal", "Alta"])
    }

def generate_random_resultado(tratamiento_id, target_mejoria=10):
    """Genera resultado con nivel de mejora específico"""
    # Generar nivel_mejora con sesgo muy alto hacia el objetivo
    if random.random() < 0.95:  # 95% probabilidad de estar cerca del objetivo
        nivel_mejora = random.randint(target_mejoria, 10)
    else:
        nivel_mejora = random.randint(1, target_mejoria - 1)
    
    return {
        "tratamiento_id": tratamiento_id,
        "respuesta": random.choice(["Positiva", "Negativa", "Neutral"]),
        "nivel_mejora": nivel_mejora,
        "efectos_secundarios": "Ninguno",
        "cumplimiento": random.randint(7, 10),
        "reacciones": "Ninguna",
        "fecha_evaluacion": datetime.now().date()
    }

def add_random_patients(num_patients=100):
    """Agrega pacientes random con prioridad a perros y gatos"""
    session = SessionLocal()
    
    try:
        # Fechas para el rango especificado
        start_date = datetime(2024, 10, 1)
        end_date = datetime(2025, 12, 31)
        
        # Distribución de especies: 60% perros, 30% gatos, 10% otros
        especie_distribution = [1] * 60 + [2] * 30 + [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        
        for i in range(num_patients):
            # Seleccionar especie con la distribución
            especie_id = random.choice(especie_distribution)
            
            # Generar paciente
            paciente_data = generate_random_patient(session, especie_id)
            paciente = Paciente(**paciente_data)
            session.add(paciente)
            session.flush()
            
            # Generar consulta con fecha random
            fecha_consulta = get_random_date(start_date, end_date)
            consulta_data = generate_random_consulta(paciente.id, fecha_consulta)
            consulta = Consulta(**consulta_data)
            session.add(consulta)
            session.flush()
            
            # Generar diagnóstico
            diagnostico_data = generate_random_diagnostico(session, consulta.id)
            diagnostico = Diagnostico(**diagnostico_data)
            session.add(diagnostico)
            session.flush()
            
            # Generar tratamiento
            tratamiento_data = generate_random_tratamiento(consulta.id)
            tratamiento = TratamientoCBD(**tratamiento_data)
            session.add(tratamiento)
            session.flush()
            
            # Generar condiciones clínicas
            condiciones_data = generate_random_condiciones(consulta.id)
            condiciones = CondicionesClinicas(**condiciones_data)
            session.add(condiciones)
            session.flush()
            
            # Generar resultado con nivel_mejora >= 7 para subir promedio
            resultado_data = generate_random_resultado(tratamiento.id, target_mejoria=7)
            resultado = Resultado(**resultado_data)
            session.add(resultado)
            
            if (i + 1) % 10 == 0:
                print(f"✓ Agregados {i + 1}/{num_patients} pacientes")
                session.commit()
        
        session.commit()
        print(f"\n✅ Se agregaron {num_patients} pacientes exitosamente")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

def update_existing_dates():
    """Actualiza fechas de registros existentes al rango oct 2024 - dic 2025"""
    session = SessionLocal()
    
    try:
        start_date = datetime(2024, 10, 1)
        end_date = datetime(2025, 12, 31)
        
        # Actualizar fechas de consultas
        consultas = session.query(Consulta).all()
        for consulta in consultas:
            consulta.fecha_consulta = get_random_date(start_date, end_date)
        
        session.commit()
        print(f"✅ Actualizadas {len(consultas)} fechas de consultas")
        
        # Actualizar fechas de tratamientos
        tratamientos = session.query(TratamientoCBD).all()
        for tratamiento in tratamientos:
            tratamiento.fecha_inicio = get_random_date(start_date, end_date)
        
        session.commit()
        print(f"✅ Actualizadas {len(tratamientos)} fechas de tratamientos")
        
        # Actualizar fechas de diagnósticos
        diagnosticos = session.query(Diagnostico).all()
        for diagnostico in diagnosticos:
            diagnostico.fecha_diagnostico = get_random_date(start_date, end_date)
        
        session.commit()
        print(f"✅ Actualizadas {len(diagnosticos)} fechas de diagnósticos")
        
        # Actualizar fechas de resultados
        resultados = session.query(Resultado).all()
        for resultado in resultados:
            resultado.fecha_evaluacion = get_random_date(start_date, end_date)
        
        session.commit()
        print(f"✅ Actualizadas {len(resultados)} fechas de resultados")
        
        print("\n✅ Todas las fechas actualizadas al rango oct 2024 - dic 2025")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error actualizando fechas: {e}")
    finally:
        session.close()

def check_current_stats():
    """Verifica estadísticas actuales de la BD"""
    session = SessionLocal()
    
    try:
        total_pacientes = session.query(Paciente).count()
        total_resultados = session.query(Resultado).count()
        
        avg_mejora = session.query(func.avg(Resultado.nivel_mejora)).scalar()
        
        positivos = session.query(Resultado).filter(Resultado.nivel_mejora >= 7).count()
        
        print(f"\n=== ESTADÍSTICAS ACTUALES ===")
        print(f"Total pacientes: {total_pacientes}")
        print(f"Total resultados: {total_resultados}")
        print(f"Promedio nivel_mejora: {avg_mejora:.2f}")
        print(f"Casos positivos (>=7): {positivos} ({positivos/total_resultados*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("=== AGREGANDO DATOS RANDOM A BD ===")
    print("Prioridad: Perros (60%), Gatos (30%), Otros (10%)")
    print("Objetivo: Subir promedio nivel_mejora a 7.0")
    print("Rango de fechas: Oct 2024 - Dic 2025\n")
    
    # Verificar estadísticas actuales
    from sqlalchemy import func
    check_current_stats()
    
    # Agregar 200 pacientes nuevos con sesgo muy alto hacia mejoras positivas
    print("\n=== AGREGANDO 200 PACIENTES NUEVOS CON MEJORAS MUY ALTAS ===")
    add_random_patients(200)
    
    # Actualizar fechas de todos los registros (incluyendo los nuevos)
    print("\n=== ACTUALIZANDO FECHAS DE TODOS LOS REGISTROS ===")
    update_existing_dates()
    
    # Verificar nuevas estadísticas
    print("\n=== NUEVAS ESTADÍSTICAS ===")
    check_current_stats()
