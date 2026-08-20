"""Script para arreglar autoincrement en todas las tablas."""

from database import get_db_session
from sqlalchemy import text

def fix_all_autoincrements():
    db = get_db_session()
    tables = ['diagnostico', 'tratamiento_cbd', 'condiciones_clinicas', 'resultado']
    
    try:
        for table in tables:
            seq_name = f"{table}_id_seq"
            
            # Crear secuencia si no existe
            db.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name}"))
            db.commit()
            
            # Asociar secuencia a columna id
            db.execute(text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{seq_name}')"))
            db.commit()
            
            # Establecer valor inicial
            db.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"))
            db.commit()
            
            print(f"✅ Autoincrement arreglado en tabla {table}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_autoincrements()
