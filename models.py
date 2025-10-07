from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Propietario(Base):
    __tablename__ = "propietario"

    id_propietario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(Text)

    pacientes: Mapped[list["Paciente"]] = relationship(
        back_populates="propietario", cascade="all, delete-orphan"
    )


class Paciente(Base):
    __tablename__ = "paciente"

    id_paciente: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    especie: Mapped[str] = mapped_column(String(50), nullable=False)
    raza: Mapped[str | None] = mapped_column(String(50))
    sexo: Mapped[str | None] = mapped_column(String(10))
    edad_anios: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    id_propietario: Mapped[int] = mapped_column(Integer, ForeignKey("propietario.id_propietario"), nullable=False)

    propietario: Mapped[Propietario] = relationship(back_populates="pacientes")
    consultas: Mapped[list["Consulta"]] = relationship(
        back_populates="paciente", cascade="all, delete-orphan"
    )


class Veterinario(Base):
    __tablename__ = "veterinario"

    id_veterinario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    especialidad: Mapped[str | None] = mapped_column(String(100))

    consultas: Mapped[list["Consulta"]] = relationship("Consulta", back_populates="veterinario")


class Consulta(Base):
    __tablename__ = "consulta"

    id_consulta: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    valoracion_mejora: Mapped[int | None] = mapped_column(SmallInteger)

    id_paciente: Mapped[int] = mapped_column(Integer, ForeignKey("paciente.id_paciente"), nullable=False)
    id_veterinario: Mapped[int] = mapped_column(Integer, ForeignKey("veterinario.id_veterinario"), nullable=False)

    paciente: Mapped[Paciente] = relationship(back_populates="consultas")
    veterinario: Mapped[Veterinario] = relationship(back_populates="consultas")
    parametros: Mapped[list["ParametroClinico"]] = relationship(
        back_populates="consulta", cascade="all, delete-orphan"
    )
    tratamientos: Mapped[list["TratamientoCBD"]] = relationship(
        back_populates="consulta", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("valoracion_mejora BETWEEN 1 AND 10", name="chk_valoracion_rango"),
    )


class ParametroClinico(Base):
    __tablename__ = "parametro_clinico"

    id_parametro: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_consulta: Mapped[int] = mapped_column(Integer, ForeignKey("consulta.id_consulta"), nullable=False)
    nombre_parametro: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    unidad: Mapped[str | None] = mapped_column(String(20))

    consulta: Mapped[Consulta] = relationship(back_populates="parametros")


class ProductoCBD(Base):
    __tablename__ = "producto_cbd"
    __table_args__ = (UniqueConstraint("nombre_comercial", name="uq_producto_nombre"),)

    id_producto: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_comercial: Mapped[str] = mapped_column(String(100), nullable=False)
    concentracion_mg_ml: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    fabricante: Mapped[str | None] = mapped_column(String(100))

    tratamientos: Mapped[list["TratamientoCBD"]] = relationship("TratamientoCBD", back_populates="producto")


class TratamientoCBD(Base):
    __tablename__ = "tratamiento_cbd"

    id_tratamiento: Mapped[int] = mapped_column(Integer, primary_key=True)
    dosis_mg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    frecuencia: Mapped[str | None] = mapped_column(String(50))
    duracion_dias: Mapped[int | None] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)

    id_consulta: Mapped[int] = mapped_column(Integer, ForeignKey("consulta.id_consulta"), nullable=False)
    id_producto: Mapped[int] = mapped_column(Integer, ForeignKey("producto_cbd.id_producto"), nullable=False)

    consulta: Mapped[Consulta] = relationship(back_populates="tratamientos")
    producto: Mapped[ProductoCBD] = relationship(back_populates="tratamientos")
