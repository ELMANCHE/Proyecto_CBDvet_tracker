"""Limpieza y validación de datos."""

from typing import Dict, Any
import numpy as np
import pandas as pd

from logger import get_logger

logger = get_logger("etl.clean")


def validate(df: pd.DataFrame) -> Dict[str, Any]:
    issues = {"weight_anomalies": 0, "age_anomalies": 0, "dosis_anomalies": 0}
    peso_col = "peso_kg" if "peso_kg" in df.columns else "peso"
    if peso_col in df.columns:
        w = df[peso_col].fillna(0)
        issues["weight_anomalies"] = int(((w <= 0) | (w > 150)).sum())
    if "edad_anios" in df.columns:
        a = df["edad_anios"].fillna(0)
        issues["age_anomalies"] = int(((a < 0) | (a > 30)).sum())
    if "dosis_mg_kg" in df.columns:
        d = df["dosis_mg_kg"].fillna(0)
        issues["dosis_anomalies"] = int(((d <= 0) | (d > 500)).sum())
    logger.info(f"Validation issues: {sum(issues.values())}")
    return issues


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    id_col = "consulta_id" if "consulta_id" in out.columns else None
    if id_col:
        out = out.drop_duplicates(subset=[id_col], keep="last")

    for col in out.select_dtypes(include=[np.number]).columns:
        med = out[col].median()
        if not pd.isna(med):
            out[col] = out[col].fillna(med)

    for col in out.select_dtypes(include=["object"]).columns:
        mode = out[col].mode()
        if len(mode):
            out[col] = out[col].fillna(mode.iloc[0])

    peso_col = "peso_kg" if "peso_kg" in out.columns else "peso"
    if peso_col in out.columns:
        out = out[(out[peso_col] > 0) | out[peso_col].isna()]
    if "dosis_mg_kg" in out.columns:
        out = out[(out["dosis_mg_kg"] > 0) | out["dosis_mg_kg"].isna()]

    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")

    logger.info(f"Cleaned: {len(out)} rows")
    return out
