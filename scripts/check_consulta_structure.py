"""Script para verificar estructura de tabla consulta."""

from database import get_db_session
from sqlalchemy import text

def check_consulta():
    db = get_db_session()
    try:
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'consulta'
            ORDER BY ordinal_position
        """))
        
        print("ESTRUCTURA TABLA CONSULTA:")
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"  {row[0]}: {row[1]} ({nullable}) default: {row[3]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_consulta()
