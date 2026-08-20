"""Script para permitir NULL en raza_id de paciente."""

from database import get_db_session
from sqlalchemy import text

def fix_raza_id():
    db = get_db_session()
    try:
        # Permitir NULL en raza_id
        db.execute(text("ALTER TABLE paciente ALTER COLUMN raza_id DROP NOT NULL"))
        db.commit()
        print("✅ raza_id ahora permite NULL")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_raza_id()
