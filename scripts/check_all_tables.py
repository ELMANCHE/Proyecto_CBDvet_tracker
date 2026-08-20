"""Script para verificar restricciones NOT NULL en todas las tablas."""

from database import get_db_session
from sqlalchemy import text

def check_all_tables():
    db = get_db_session()
    tables = ['paciente', 'consulta', 'diagnostico', 'tratamiento_cbd', 'condiciones_clinicas', 'resultado']
    
    try:
        for table in tables:
            result = db.execute(text(f"""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND is_nullable = 'NO'
                ORDER BY ordinal_position
            """))
            
            not_null_cols = [row[0] for row in result]
            print(f"{table.upper()} - NOT NULL columns: {not_null_cols}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_tables()
