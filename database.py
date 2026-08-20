"""SQLAlchemy ORM alineado con el schema PostgreSQL actual."""

from datetime import datetime, date
from typing import Generator, Optional

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, create_engine, text,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from config import config
from logger import get_logger

logger = get_logger(__name__)

engine = create_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TipoEspecie(Base):
    __tablename__ = "tipo_especie"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    nombre_cientifico = Column(String(100))
    activo = Column(Boolean, default=True)

    razas = relationship("Raza", back_populates="especie")
    pacientes = relationship("Paciente", back_populates="especie")


class Raza(Base):
    __tablename__ = "raza"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    tipo_especie_id = Column(Integer, ForeignKey("tipo_especie.id"), nullable=False)

    especie = relationship("TipoEspecie", back_populates="razas")
    pacientes = relationship("Paciente", back_populates="raza")

    __table_args__ = (Index("ix_raza_especie", "tipo_especie_id"),)


class Paciente(Base):
    __tablename__ = "paciente"

    id = Column(Integer, primary_key=True, server_default=text("nextval('paciente_id_seq')"))
    tipo_especie_id = Column(Integer, ForeignKey("tipo_especie.id"), nullable=False)
    raza_id = Column(Integer, ForeignKey("raza.id"))
    sexo = Column(String(10))
    fecha_nacimiento = Column(Date)
    esterilizado = Column(Boolean)
    codigo_paciente = Column(String(20), unique=True)
    color = Column(String(30))
    peso_base = Column(Float)
    fecha_registro = Column(Date, default=date.today)
    activo = Column(Boolean, default=True)

    especie = relationship("TipoEspecie", back_populates="pacientes")
    raza = relationship("Raza", back_populates="pacientes")
    consultas = relationship("Consulta", back_populates="paciente")

    __table_args__ = (
        Index("ix_paciente_especie", "tipo_especie_id"),
        Index("ix_paciente_codigo", "codigo_paciente"),
    )


class Consulta(Base):
    __tablename__ = "consulta"

    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("paciente.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    peso = Column(Float, nullable=False)
    motivo = Column(Text)
    temperatura = Column(Float)
    frecuencia_cardiaca = Column(Integer)
    observaciones = Column(Text)

    paciente = relationship("Paciente", back_populates="consultas")
    diagnosticos = relationship("Diagnostico", back_populates="consulta")
    tratamientos = relationship("TratamientoCBD", back_populates="consulta")
    condiciones = relationship("CondicionesClinicas", back_populates="consulta")
    contexto = relationship("Contexto", back_populates="consulta", uselist=False)

    __table_args__ = (
        Index("ix_consulta_paciente", "paciente_id"),
        Index("ix_consulta_fecha", "fecha"),
    )


class Enfermedad(Base):
    __tablename__ = "enfermedad"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(50))
    descripcion = Column(Text)

    diagnosticos = relationship("Diagnostico", back_populates="enfermedad")


class Diagnostico(Base):
    __tablename__ = "diagnostico"

    id = Column(Integer, primary_key=True)
    consulta_id = Column(Integer, ForeignKey("consulta.id"), nullable=False)
    enfermedad_id = Column(Integer, ForeignKey("enfermedad.id"), nullable=False)
    severidad = Column(String(50))
    duracion_dias = Column(Integer)

    consulta = relationship("Consulta", back_populates="diagnosticos")
    enfermedad = relationship("Enfermedad", back_populates="diagnosticos")

    __table_args__ = (Index("ix_diagnostico_consulta", "consulta_id"),)


class TratamientoCBD(Base):
    __tablename__ = "tratamiento_cbd"

    id = Column(Integer, primary_key=True)
    consulta_id = Column(Integer, ForeignKey("consulta.id"), nullable=False)
    dosis_mg_kg = Column(Float, nullable=False)
    frecuencia = Column(String(50))
    duracion_dias = Column(Integer)
    tipo_producto = Column(String(100))
    concentracion = Column(String(100))
    dosis_mg = Column(Float)
    via_administracion = Column(String(30))
    tipo_extracto = Column(String(30))
    fecha_inicio = Column(Date)

    consulta = relationship("Consulta", back_populates="tratamientos")
    resultados = relationship("Resultado", back_populates="tratamiento")

    __table_args__ = (Index("ix_tratamiento_consulta", "consulta_id"),)


class CondicionesClinicas(Base):
    __tablename__ = "condiciones_clinicas"

    id = Column(Integer, primary_key=True)
    consulta_id = Column(Integer, ForeignKey("consulta.id"), nullable=False)
    comorbilidades = Column(String(100))
    medicamentos_previos = Column(String(100))
    estado_nutricional = Column(Integer)
    presion_arterial = Column(Integer)
    alt = Column(Integer)
    ast = Column(Integer)
    nivel_estres = Column(Integer)
    tipo_dolor = Column(String(50))
    actividad_fisica = Column(String(50))
    apetito = Column(String(50))
    hidratacion = Column(String(50))

    consulta = relationship("Consulta", back_populates="condiciones")


class Resultado(Base):
    __tablename__ = "resultado"

    id = Column(Integer, primary_key=True)
    tratamiento_id = Column(Integer, ForeignKey("tratamiento_cbd.id"), nullable=False)
    respuesta = Column(String(20))
    nivel_mejora = Column(Integer)
    efectos_secundarios = Column(String(50))
    cumplimiento = Column(Integer)
    reacciones = Column(Text)
    fecha_evaluacion = Column(Date)

    tratamiento = relationship("TratamientoCBD", back_populates="resultados")

    __table_args__ = (Index("ix_resultado_tratamiento", "tratamiento_id"),)


class Contexto(Base):
    __tablename__ = "contexto"

    id = Column(Integer, primary_key=True)
    consulta_id = Column(Integer, ForeignKey("consulta.id"), nullable=False)
    epoca = Column(String(20))
    ubicacion = Column(String(100))
    precio = Column(Float)
    marca = Column(String(50))
    tipo_alimentacion = Column(String(50))

    consulta = relationship("Consulta", back_populates="contexto")


class StagingCarga(Base):
    """Tabla staging para carga masiva previa a validación."""
    __tablename__ = "staging_carga"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(36), nullable=False, index=True)
    fila_num = Column(Integer)
    payload = Column(Text, nullable=False)
    estado = Column(String(20), default="pendiente")  # pendiente|valido|error|procesado
    errores = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Auditoría de cambios en entidades."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    entidad = Column(String(50), nullable=False)
    entidad_id = Column(Integer)
    accion = Column(String(20), nullable=False)  # CREATE|UPDATE|DELETE
    usuario = Column(String(100))
    datos = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_entidad", "entidad", "entidad_id"),
        Index("ix_audit_fecha", "created_at"),
    )


class Usuario(Base):
    """Usuarios API con roles."""
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    api_key = Column(String(64), nullable=False, unique=True)
    rol = Column(String(20), default="viewer")  # admin|editor|viewer
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db_session() -> Session:
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea tablas ORM que no existen (staging, audit, usuario). No toca tablas legacy."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")


def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
