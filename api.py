"""
CBD Veterinary Prediction API — CRUD + ML + Staging + Auth
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import config
from database import get_db, init_db, test_connection, StagingCarga
from logger import get_logger
from etl import ETLPipeline
from ml.pipeline import load_latest_preprocessor
from ml.shap_explainer import explain_prediction
from api.schemas import (
    PacienteCreate, PacienteOut, ConsultaCreate, ConsultaOut,
    TratamientoCreate, TratamientoOut, ResultadoCreate, ResultadoOut,
    CasoCompletoCreate, CasoCompletoOut, PatientInfo, PredictionResponse,
    BulkUploadRequest, BulkUploadResponse, AnalyticsResponse,
)
from api.crud import (
    create_paciente, get_paciente, list_pacientes,
    create_consulta, get_consulta, list_consultas,
    create_tratamiento, create_resultado, create_caso_completo,
)
from api.auth import get_current_user, require_role, seed_default_user
from ml.feature_engineering import engineer_patient_features

logger = get_logger(__name__)

app = FastAPI(title="CBD Tracker API", version="2.0.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Model Manager ────────────────────────────────────────────────────────────

class ModelManager:
    def __init__(self):
        self.models = {}
        self.feature_names = []
        self.preprocessor = None
        self._load()

    def _load(self):
        # Solo cargar XGBoost (mejor modelo)
        files = sorted(config.MODELS_DIR.glob("xgboost_v*.joblib"))
        if files:
            self.models["xgboost"] = joblib.load(files[-1])
            logger.info(f"Loaded XGBoost: {files[-1].name}")
        else:
            logger.warning("No XGBoost model found")

        meta_files = sorted(config.MODELS_DIR.glob("dataset_meta_v*.joblib"))
        results_files = sorted(config.MODELS_DIR.glob("training_results_*.joblib"))
        if meta_files:
            meta = joblib.load(meta_files[-1])
            self.feature_names = meta.get("feature_names", [])
        elif results_files:
            res = joblib.load(results_files[-1])
            if isinstance(res, dict):
                self.feature_names = res.get("feature_names", [])

        self.preprocessor, _ = load_latest_preprocessor()

    def predict(self, X: pd.DataFrame, model_name: str = "xgboost", threshold: float = 0.35) -> dict:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")
        model = self.models[model_name]
        cols = [c for c in self.feature_names if c in X.columns] if self.feature_names else X.columns.tolist()
        X_use = X[cols] if cols else X

        if self.preprocessor:
            try:
                X_use = pd.DataFrame(self.preprocessor.transform(X_use), columns=X_use.columns)
            except Exception:
                pass

        proba = model.predict_proba(X_use)[0] if hasattr(model, "predict_proba") else [0.5, 0.5]
        # Usar umbral personalizado para predicción (más bajo para ser más optimista)
        pred = 1 if proba[1] >= threshold else 0
        return {
            "prediction": pred,
            "probabilidad_mejora": float(proba[1]),  # Solo probabilidad de mejoría
            "model_name": "XGBoost Classifier",  # Nombre del modelo único
            "X": X_use.values,
            "feature_names": list(X_use.columns),
        }


model_manager = ModelManager()


def engineer_features(patient: PatientInfo) -> pd.DataFrame:
    """
    Genera features usando el módulo centralizado de feature engineering
    
    Esta función ahora delega al módulo ml.feature_engineering para garantizar
    consistencia entre entrenamiento y predicción.
    """
    # Convertir PatientInfo a diccionario
    patient_dict = {
        "especie": patient.especie,
        "peso_kg": patient.peso_kg,
        "sexo": patient.sexo,
        "edad_anios": patient.edad_anios,
        "enfermedad": patient.enfermedad,
        "severidad": patient.severidad,
        "duracion_dias": patient.duracion_dias,
        "dosis_mg_kg": patient.dosis_mg_kg,
        "frecuencia": patient.frecuencia,
        "tipo_producto": patient.tipo_producto,
        "estado_nutricional": patient.estado_nutricional,
        "nivel_estres": patient.nivel_estres,
        "cumplimiento": patient.cumplimiento,
        "alt": patient.alt,
        "ast": patient.ast,
    }
    
    # Usar el módulo centralizado
    df = engineer_patient_features(patient_dict)
    
    # Asegurar compatibilidad con feature_names del model_manager
    if model_manager.feature_names:
        for c in model_manager.feature_names:
            if c not in df.columns:
                df[c] = 0
        df = df[model_manager.feature_names]
    
    return df.fillna(0)


def recommendation(pred: int, conf: float, patient: PatientInfo) -> str:
    if pred == 1:
        return f"Potencial de mejoría ({conf:.0%}). Dosis: {patient.dosis_mg_kg} mg/kg."
    return f"Bajo potencial ({conf:.0%}). Considerar ajuste de dosis o tratamiento alternativo."


@app.on_event("startup")
def startup():
    init_db()
    db = next(get_db())
    try:
        seed_default_user(db)
    finally:
        db.close()


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_available": list(model_manager.models.keys()),
        "database_connected": test_connection(),
        "version": "2.0.0",
    }


# ── CRUD Pacientes ───────────────────────────────────────────────────────────

@app.get("/pacientes", response_model=List[PacienteOut])
def api_list_pacientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                       _user=Depends(get_current_user)):
    return list_pacientes(db, skip, limit)


@app.post("/pacientes", response_model=PacienteOut)
def api_create_paciente(data: PacienteCreate, db: Session = Depends(get_db),
                         user=Depends(require_role("admin", "editor"))):
    obj = create_paciente(db, data, user.username)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/pacientes/{paciente_id}", response_model=PacienteOut)
def api_get_paciente(paciente_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    obj = get_paciente(db, paciente_id)
    if not obj:
        raise HTTPException(404, "Paciente no encontrado")
    return obj


# ── CRUD Consultas ───────────────────────────────────────────────────────────

@app.get("/consultas", response_model=List[ConsultaOut])
def api_list_consultas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                       _user=Depends(get_current_user)):
    return list_consultas(db, skip, limit)


@app.post("/consultas", response_model=ConsultaOut)
def api_create_consulta(data: ConsultaCreate, db: Session = Depends(get_db),
                        user=Depends(require_role("admin", "editor"))):
    obj = create_consulta(db, data, user.username)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/consultas/{consulta_id}", response_model=ConsultaOut)
def api_get_consulta(consulta_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    obj = get_consulta(db, consulta_id)
    if not obj:
        raise HTTPException(404, "Consulta no encontrada")
    return obj


# ── CRUD Tratamientos / Resultados ───────────────────────────────────────────

@app.post("/tratamientos", response_model=TratamientoOut)
def api_create_tratamiento(data: TratamientoCreate, db: Session = Depends(get_db),
                           user=Depends(require_role("admin", "editor"))):
    obj = create_tratamiento(db, data, user.username)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/resultados", response_model=ResultadoOut)
def api_create_resultado(data: ResultadoCreate, db: Session = Depends(get_db),
                         user=Depends(require_role("admin", "editor"))):
    obj = create_resultado(db, data, user.username)
    db.commit()
    db.refresh(obj)
    return obj


# ── Caso completo ────────────────────────────────────────────────────────────

@app.post("/casos/completo", response_model=CasoCompletoOut)
def api_caso_completo(data: CasoCompletoCreate, db: Session = Depends(get_db),
                      user=Depends(require_role("admin", "editor"))):
    ids = create_caso_completo(db, data, user.username)
    return CasoCompletoOut(**ids)


# ── Bulk / Staging ───────────────────────────────────────────────────────────

@app.post("/bulk/upload", response_model=BulkUploadResponse)
def api_bulk_upload(req: BulkUploadRequest, db: Session = Depends(get_db),
                    user=Depends(require_role("admin", "editor"))):
    import uuid
    batch_id = str(uuid.uuid4())
    validos = errores = 0
    for i, rec in enumerate(req.records):
        try:
            rec.model_validate(rec.model_dump())
            db.add(StagingCarga(batch_id=batch_id, fila_num=i + 1,
                                payload=json.dumps(rec.model_dump()), estado="valido"))
            validos += 1
        except Exception as e:
            db.add(StagingCarga(batch_id=batch_id, fila_num=i + 1,
                                payload=json.dumps(rec.model_dump(), default=str),
                                estado="error", errores=str(e)))
            errores += 1
    db.commit()
    return BulkUploadResponse(batch_id=batch_id, total=len(req.records), validos=validos, errores=errores)


@app.post("/bulk/process/{batch_id}")
def api_bulk_process(batch_id: str, db: Session = Depends(get_db),
                     user=Depends(require_role("admin"))):
    rows = db.query(StagingCarga).filter_by(batch_id=batch_id, estado="valido").all()
    processed = 0
    for row in rows:
        data = CasoCompletoCreate(**json.loads(row.payload))
        create_caso_completo(db, data, user.username)
        row.estado = "procesado"
        processed += 1
    db.commit()
    return {"batch_id": batch_id, "processed": processed}


# ── Analytics / Dataset ──────────────────────────────────────────────────────

@app.get("/analytics", response_model=AnalyticsResponse)
def api_analytics(
    especie: Optional[str] = None,
    enfermedad: Optional[str] = None,
    dosis_min: Optional[float] = None,
    dosis_max: Optional[float] = None,
    _user=Depends(get_current_user),
):
    df = ETLPipeline().extract_data()
    
    # Ordenar por consulta_id para mantener orden consistente
    if "consulta_id" in df.columns:
        df = df.sort_values("consulta_id").reset_index(drop=True)
    
    if especie and "especie" in df.columns:
        df = df[df["especie"] == especie]
    if enfermedad and "enfermedad" in df.columns:
        df = df[df["enfermedad"] == enfermedad]
    if dosis_min is not None:
        df = df[df["dosis_mg_kg"] >= dosis_min]
    if dosis_max is not None:
        df = df[df["dosis_mg_kg"] <= dosis_max]

    mejora_col = "nivel_mejora" if "nivel_mejora" in df.columns else None
    mejora_media = float(df[mejora_col].mean()) if mejora_col else 0.0
    pct_sig = float((df[mejora_col] >= 7).mean() * 100) if mejora_col else 0.0

    # Devolver todos los registros, no solo 100
    records = df.replace({np.nan: None}).to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    return AnalyticsResponse(
        total=len(df), mejora_media=mejora_media,
        pct_significativa=pct_sig, records=records,
    )


@app.get("/catalogos/especies")
def catalogo_especies(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    from database import TipoEspecie
    return [{"id": e.id, "nombre": e.nombre} for e in db.query(TipoEspecie).all()]


@app.get("/catalogos/enfermedades")
def catalogo_enfermedades(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    from database import Enfermedad
    return [{"id": e.id, "nombre": e.nombre} for e in db.query(Enfermedad).all()]


# ── ML Predict ───────────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse)
def predict(patient: PatientInfo, model: str = "xgboost", explain: bool = False, threshold: float = 0.35,
            _user=Depends(get_current_user)):
    try:
        X = engineer_features(patient)
        result = model_manager.predict(X, model_name=model, threshold=threshold)
        rec = recommendation(result["prediction"], result["probabilidad_mejora"], patient)

        # Datos relevantes para el usuario
        datos_paciente = {
            "especie": patient.especie,
            "peso_kg": patient.peso_kg,
            "edad_anios": patient.edad_anios,
            "enfermedad": patient.enfermedad,
            "severidad": patient.severidad,
            "dosis_mg_kg": patient.dosis_mg_kg,
            "frecuencia": patient.frecuencia,
            "nivel_estres": patient.nivel_estres,
            "estado_nutricional": patient.estado_nutricional,
        }

        return PredictionResponse(
            timestamp=datetime.now().isoformat(),
            prediction=result["prediction"],
            probabilidad_mejora=result["probabilidad_mejora"],
            model_name=result["model_name"],
            features_used=len(result["feature_names"]),
            recommendation=rec,
            datos_paciente=datos_paciente,
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/models")
def list_models(_user=Depends(get_current_user)):
    return {"models": list(model_manager.models.keys())}


if __name__ == "__main__":
    logger.info("Launching CBD API v2...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
