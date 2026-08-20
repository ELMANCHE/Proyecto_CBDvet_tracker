"""Script para arreglar autoincrement en tabla consulta."""

from database import get_db_session
from sqlalchemy import text

def fix_consulta_id():
    db = get_db_session()
    try:
        # Crear secuencia si no existe
        db.execute(text("CREATE SEQUENCE IF NOT EXISTS consulta_id_seq"))
        db.commit()
        
        # Asociar secuencia a columna id
        db.execute(text("ALTER TABLE consulta ALTER COLUMN id SET DEFAULT nextval('consulta_id_seq')"))
        db.commit()
        
        # Establecer valor inicial
        db.execute(text("SELECT setval('consulta_id_seq', COALESCE((SELECT MAX(id) FROM consulta), 0) + 1, false)"))
        db.commit()
        
        print("✅ Autoincrement arreglado en tabla consulta")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_consulta_id()
