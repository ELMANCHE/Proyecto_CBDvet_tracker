"""Script para arreglar autoincrement en tabla paciente."""

from database import get_db_session
from sqlalchemy import text

def fix_paciente_id():
    db = get_db_session()
    try:
        # Crear secuencia si no existe
        db.execute(text("CREATE SEQUENCE IF NOT EXISTS paciente_id_seq"))
        db.commit()
        
        # Asociar secuencia a columna id
        db.execute(text("ALTER TABLE paciente ALTER COLUMN id SET DEFAULT nextval('paciente_id_seq')"))
        db.commit()
        
        # Establecer valor inicial
        db.execute(text("SELECT setval('paciente_id_seq', COALESCE((SELECT MAX(id) FROM paciente), 0) + 1, false)"))
        db.commit()
        
        print("✅ Autoincrement arreglado en tabla paciente")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_paciente_id()
