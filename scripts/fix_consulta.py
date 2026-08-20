"""Script para permitir NULL en campos opcionales de consulta."""

from database import get_db_session
from sqlalchemy import text

def fix_consulta():
    db = get_db_session()
    try:
        # Permitir NULL en campos opcionales
        db.execute(text("ALTER TABLE consulta ALTER COLUMN temperatura DROP NOT NULL"))
        db.execute(text("ALTER TABLE consulta ALTER COLUMN frecuencia_cardiaca DROP NOT NULL"))
        db.execute(text("ALTER TABLE consulta ALTER COLUMN observaciones DROP NOT NULL"))
        db.commit()
        print("✅ Campos opcionales de consulta ahora permiten NULL")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_consulta()
