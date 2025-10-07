import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql+psycopg2://cbdvet_user:cbdvet_pass@localhost:5432/cbdvet_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(DATABASE_URL, future=True, echo=False)

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos."""


@contextmanager
def session_scope():
    """Proporciona un contexto transaccional para una sesión de base de datos."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Inicializa la base de datos creando las tablas definidas."""
    from models import (  # noqa: F401
        Propietario,
        Paciente,
        Veterinario,
        Consulta,
        ParametroClinico,
        ProductoCBD,
        TratamientoCBD,
    )

    Base.metadata.create_all(bind=engine)
