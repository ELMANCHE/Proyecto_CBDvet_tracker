"""Pydantic schemas para la API."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ── Paciente ─────────────────────────────────────────────────────────────────

class PacienteCreate(BaseModel):
    tipo_especie_id: int
    raza_id: Optional[int] = None
    sexo: str = Field(..., pattern="^[MF]$")
    edad_anios: float = Field(..., ge=0, le=30)
    esterilizado: bool = False
    codigo_paciente: Optional[str] = None
    color: Optional[str] = None
    peso_base: Optional[float] = None


class PacienteOut(BaseModel):
    id: int
    tipo_especie_id: int
    raza_id: Optional[int]
    sexo: Optional[str]
    codigo_paciente: Optional[str]
    activo: Optional[bool]

    class Config:
        from_attributes = True


# ── Consulta ─────────────────────────────────────────────────────────────────

class ConsultaCreate(BaseModel):
    paciente_id: int
    peso: float = Field(..., gt=0, le=150)
    motivo: Optional[str] = None
    temperatura: Optional[float] = None
    frecuencia_cardiaca: Optional[int] = None
    observaciones: Optional[str] = None


class ConsultaOut(BaseModel):
    id: int
    paciente_id: int
    fecha: Optional[datetime]
    peso: float
    motivo: Optional[str]

    class Config:
        from_attributes = True


# ── Diagnóstico ──────────────────────────────────────────────────────────────

class DiagnosticoCreate(BaseModel):
    consulta_id: int
    enfermedad_id: int
    severidad: str = Field(..., pattern="^(Leve|Moderada|Grave)$")
    duracion_dias: int = Field(..., ge=1, le=3650)


# ── Tratamiento ──────────────────────────────────────────────────────────────

class TratamientoCreate(BaseModel):
    consulta_id: int
    dosis_mg_kg: float = Field(..., gt=0, le=500)
    frecuencia: str = "Diaria"
    duracion_dias: int = Field(30, ge=1)
    tipo_producto: str = "Aceite"
    via_administracion: Optional[str] = None


class TratamientoOut(BaseModel):
    id: int
    consulta_id: int
    dosis_mg_kg: float
    frecuencia: Optional[str]
    tipo_producto: Optional[str]

    class Config:
        from_attributes = True


# ── Resultado ────────────────────────────────────────────────────────────────

class ResultadoCreate(BaseModel):
    tratamiento_id: int
    respuesta: str = "Parcial"
    nivel_mejora: int = Field(..., ge=1, le=10)
    cumplimiento: int = Field(100, ge=0, le=100)
    efectos_secundarios: Optional[str] = None


class ResultadoOut(BaseModel):
    id: int
    tratamiento_id: int
    respuesta: Optional[str]
    nivel_mejora: Optional[int]

    class Config:
        from_attributes = True


# ── Caso completo (Streamlit) ────────────────────────────────────────────────

class CasoCompletoCreate(BaseModel):
    tipo_especie_id: int
    sexo: str
    edad_anios: float = Field(..., ge=0, le=30)
    peso_kg: float = Field(..., gt=0, le=150)
    enfermedad_id: int
    severidad: str = "Moderada"
    duracion_dias: int = 90
    dosis_mg_kg: float = Field(..., gt=0, le=500)
    frecuencia: str = "Diaria"
    tipo_producto: str = "Aceite"
    estado_nutricional: int = 1
    nivel_estres: int = Field(5, ge=0, le=10)
    cumplimiento: int = Field(100, ge=0, le=100)
    nivel_mejora: Optional[int] = None


class CasoCompletoOut(BaseModel):
    consulta_id: int
    paciente_id: int
    tratamiento_id: int
    prediction: Optional[Dict[str, Any]] = None


# ── Predicción ───────────────────────────────────────────────────────────────

class PatientInfo(BaseModel):
    especie: str
    peso_kg: float = Field(..., ge=0.5, le=150)
    sexo: str = Field(..., pattern="^[MF]$")
    edad_anios: int = Field(..., ge=0, le=30)
    enfermedad: str
    severidad: str = "Moderada"
    duracion_dias: int = Field(180, ge=1, le=3650)
    dosis_mg_kg: float = Field(..., ge=0.1, le=500)
    frecuencia: str = "Diaria"
    tipo_producto: str = "Aceite"
    comorbilidades: Optional[str] = None
    estado_nutricional: str = "Normal"
    nivel_estres: float = Field(5.0, ge=0, le=10)
    alt: Optional[float] = None
    ast: Optional[float] = None
    cumplimiento: float = Field(1.0, ge=0, le=1)


class PredictionResponse(BaseModel):
    timestamp: str
    prediction: int
    probabilidad_mejora: float
    model_name: str
    features_used: int
    recommendation: str
    datos_paciente: Optional[Dict[str, Any]] = None  # Datos relevantes para el usuario


# ── Bulk / Staging ───────────────────────────────────────────────────────────

class BulkUploadRequest(BaseModel):
    records: List[CasoCompletoCreate]


class BulkUploadResponse(BaseModel):
    batch_id: str
    total: int
    validos: int
    errores: int


# ── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total: int
    mejora_media: float
    pct_significativa: float
    records: List[Dict[str, Any]]
