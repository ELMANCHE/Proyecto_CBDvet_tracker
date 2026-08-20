"""Script para verificar estado de tabla paciente."""

from database import get_db_session
from sqlalchemy import text

def check_paciente():
    db = get_db_session()
    try:
        # Verificar estructura de tabla
        result = db.execute(text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'paciente' 
            ORDER BY ordinal_position
        """))
        
        print("Estructura actual de tabla paciente:")
        for row in result:
            print(f"  {row[0]}: {row[1]} (default: {row[2]})")
        
        # Verificar si existe secuencia
        result = db.execute(text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_name LIKE '%paciente%'
        """))
        
        print("\nSecuencias relacionadas con paciente:")
        for row in result:
            print(f"  {row[0]}")
            
        # Verificar máximo ID actual
        result = db.execute(text("SELECT MAX(id) FROM paciente"))
        max_id = result.scalar()
        print(f"\nMáximo ID actual: {max_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_paciente()
