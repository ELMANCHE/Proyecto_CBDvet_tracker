"""Operaciones CRUD con SQLAlchemy ORM."""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from database import (
    Paciente, Consulta, Diagnostico, TratamientoCBD, Resultado,
    CondicionesClinicas, AuditLog,
)
from api.schemas import (
    PacienteCreate, ConsultaCreate, DiagnosticoCreate,
    TratamientoCreate, ResultadoCreate, CasoCompletoCreate,
)
from logger import get_logger

logger = get_logger("api.crud")


def audit(session: Session, entidad: str, entidad_id: int, accion: str, usuario: str, datos: dict):
    session.add(AuditLog(
        entidad=entidad, entidad_id=entidad_id, accion=accion,
        usuario=usuario, datos=json.dumps(datos, default=str),
    ))


def create_paciente(session: Session, data: PacienteCreate, usuario: str = "api") -> Paciente:
    obj = Paciente(
        tipo_especie_id=data.tipo_especie_id,
        raza_id=data.raza_id,
        sexo=data.sexo,
        fecha_nacimiento=date.today() - timedelta(days=int(data.edad_anios * 365.25)),
        esterilizado=data.esterilizado,
        codigo_paciente=data.codigo_paciente or f"P{datetime.now().strftime('%H%M%S%f')[:10]}",
        color=data.color,
        peso_base=data.peso_base,
        activo=True,
    )
    session.add(obj)
    session.flush()
    audit(session, "paciente", obj.id, "CREATE", usuario, data.model_dump())
    return obj


def get_paciente(session: Session, paciente_id: int) -> Optional[Paciente]:
    return session.query(Paciente).filter(Paciente.id == paciente_id).first()


def list_pacientes(session: Session, skip: int = 0, limit: int = 100) -> List[Paciente]:
    return session.query(Paciente).offset(skip).limit(limit).all()


def create_consulta(session: Session, data: ConsultaCreate, usuario: str = "api") -> Consulta:
    obj = Consulta(**data.model_dump())
    session.add(obj)
    session.flush()
    audit(session, "consulta", obj.id, "CREATE", usuario, data.model_dump())
    return obj


def get_consulta(session: Session, consulta_id: int) -> Optional[Consulta]:
    return session.query(Consulta).filter(Consulta.id == consulta_id).first()


def list_consultas(session: Session, skip: int = 0, limit: int = 100) -> List[Consulta]:
    return session.query(Consulta).order_by(Consulta.fecha.desc()).offset(skip).limit(limit).all()


def create_tratamiento(session: Session, data: TratamientoCreate, usuario: str = "api") -> TratamientoCBD:
    obj = TratamientoCBD(**data.model_dump(), fecha_inicio=date.today())
    session.add(obj)
    session.flush()
    audit(session, "tratamiento_cbd", obj.id, "CREATE", usuario, data.model_dump())
    return obj


def create_resultado(session: Session, data: ResultadoCreate, usuario: str = "api") -> Resultado:
    obj = Resultado(**data.model_dump(), fecha_evaluacion=date.today())
    session.add(obj)
    session.flush()
    audit(session, "resultado", obj.id, "CREATE", usuario, data.model_dump())
    return obj


def create_caso_completo(session: Session, data: CasoCompletoCreate, usuario: str = "api") -> dict:
    try:
        # Crear paciente
        pac = create_paciente(session, PacienteCreate(
            tipo_especie_id=data.tipo_especie_id, sexo=data.sexo,
            edad_anios=data.edad_anios, peso_base=data.peso_kg,
            raza_id=None,
        ), usuario)
        session.flush()

        # Crear consulta
        con = Consulta(
            paciente_id=pac.id, peso=data.peso_kg, motivo=f"CBD - enfermedad_id={data.enfermedad_id}"
        )
        session.add(con)
        session.flush()

        # Crear diagnostico
        diag = Diagnostico(
            consulta_id=con.id, enfermedad_id=data.enfermedad_id,
            severidad=data.severidad, duracion_dias=data.duracion_dias
        )
        session.add(diag)
        session.flush()

        # Crear tratamiento
        trat = TratamientoCBD(
            consulta_id=con.id, dosis_mg_kg=data.dosis_mg_kg,
            frecuencia=data.frecuencia, duracion_dias=data.duracion_dias,
            tipo_producto=data.tipo_producto
        )
        session.add(trat)
        session.flush()

        # Crear condiciones clinicas
        cond = CondicionesClinicas(
            consulta_id=con.id, estado_nutricional=data.estado_nutricional,
            nivel_estres=data.nivel_estres
        )
        session.add(cond)
        session.flush()

        # Crear resultado si se proporciona nivel_mejora
        if data.nivel_mejora:
            res = Resultado(
                tratamiento_id=trat.id,
                respuesta="Exitoso" if data.nivel_mejora >= 7 else "Parcial",
                nivel_mejora=data.nivel_mejora, cumplimiento=data.cumplimiento
            )
            session.add(res)
            session.flush()

        session.commit()
        return {"consulta_id": con.id, "paciente_id": pac.id, "tratamiento_id": trat.id}
    except Exception as e:
        session.rollback()
        raise Exception(f"Error creando caso completo: {str(e)}")
