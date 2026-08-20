"""Script para verificar estado de la BD."""

from database import get_db_session, TipoEspecie, Enfermedad, Paciente
from sqlalchemy import func, text

def check_bd():
    db = get_db_session()
    try:
        # Verificar especies
        especies = db.query(TipoEspecie).all()
        print("ESPECIES EN BD:")
        for e in especies:
            print(f"  ID {e.id}: {e.nombre}")
        
        # Verificar enfermedades
        enfermedades = db.query(Enfermedad).all()
        print(f"\nENFERMEDADES EN BD ({len(enfermedades)}):")
        for e in enfermedades[:10]:
            print(f"  ID {e.id}: {e.nombre}")
        
        # Verificar pacientes
        pacientes_count = db.query(func.count(Paciente.id)).scalar()
        max_paciente_id = db.query(func.max(Paciente.id)).scalar()
        print(f"\nPACIENTES:")
        print(f"  Total: {pacientes_count}")
        print(f"  Max ID: {max_paciente_id}")
        
        # Verificar estructura de tabla paciente
        result = db.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'paciente' AND column_name = 'id'
        """))
        print(f"\nESTRUCTURA COLUMNA ID:")
        for row in result:
            print(f"  {row[0]}: {row[1]} (default: {row[2]})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_bd()
