"""
Script para llenar valores faltantes de raza en la base de datos
"""

import sys
import random
from sqlalchemy.orm import Session
from database import SessionLocal, Paciente, Raza, TipoEspecie

def fill_missing_razas():
    """Llenar valores faltantes de raza basándose en la especie del paciente"""
    session = SessionLocal()
    
    try:
        # Obtener todas las razas disponibles por especie
        razas_por_especie = {}
        razas = session.query(Raza).all()
        
        for raza in razas:
            especie_id = raza.tipo_especie_id
            if especie_id not in razas_por_especie:
                razas_por_especie[especie_id] = []
            razas_por_especie[especie_id].append(raza)
        
        print(f"Razas disponibles por especie:")
        for especie_id, razas_list in razas_por_especie.items():
            especie = session.query(TipoEspecie).filter(TipoEspecie.id == especie_id).first()
            print(f"  {especie.nombre if especie else especie_id}: {len(razas_list)} razas")
        
        # Obtener pacientes sin raza
        pacientes_sin_raza = session.query(Paciente).filter(Paciente.raza_id.is_(None)).all()
        print(f"\nPacientes sin raza: {len(pacientes_sin_raza)}")
        
        # Asignar razas aleatorias basadas en la especie
        actualizados = 0
        for paciente in pacientes_sin_raza:
            especie_id = paciente.tipo_especie_id
            
            if especie_id in razas_por_especie and razas_por_especie[especie_id]:
                # Seleccionar una raza aleatoria de la especie del paciente
                raza_asignada = random.choice(razas_por_especie[especie_id])
                paciente.raza_id = raza_asignada.id
                actualizados += 1
            else:
                print(f"  Advertencia: No hay razas disponibles para especie_id {especie_id}")
        
        session.commit()
        print(f"\nRazas asignadas exitosamente: {actualizados}")
        
        # Verificar resultado
        pacientes_con_raza = session.query(Paciente).filter(Paciente.raza_id.isnot(None)).count()
        total_pacientes = session.query(Paciente).count()
        print(f"Pacientes con raza: {pacientes_con_raza}/{total_pacientes} ({pacientes_con_raza/total_pacientes*100:.1f}%)")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fill_missing_razas()
