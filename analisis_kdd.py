"""Pipeline KDD para análisis de tratamientos CBD veterinarios.

Este script extrae los datos reales de PostgreSQL, ejecuta una
preparación básica (limpieza, feature engineering), construye
agrupaciones y modelos predictivos y publica los resultados en un
cache interno que el dashboard de Streamlit consume en tiempo real.

Al ejecutarlo, mantiene un bucle que refresca los resultados cada
ciertos segundos para que el dashboard muestre la información al día.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select

from database import SessionLocal
from models import (
    Consulta,
    ParametroClinico,
    TratamientoCBD,
    Paciente,
    Veterinario,
    ProductoCBD,
)

load_dotenv()

CACHE_FILE = Path(os.getenv("ANALYTICS_CACHE", "cache/analytics.json"))
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AnalyticsResult:
    timestamp: datetime
    total_consultas: int
    total_pacientes: int
    especies: Dict[str, int]
    tratamientos_por_especie: Dict[str, float]
    clustering_resumen: List[Dict[str, Any]]
    modelo_accuracy: float
    matriz_confusion: List[List[int]]
    feature_importance: List[Dict[str, Any]]
    etl_log: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.timestamp.isoformat(),
            "totals": {
                "consultas": self.total_consultas,
                "pacientes": self.total_pacientes,
            },
            "especies": self.especies,
            "tasa_tratamiento_exitoso": self.tratamientos_por_especie,
            "clustering": self.clustering_resumen,
            "modelo_predictivo": {
                "accuracy": self.modelo_accuracy,
                "matriz_confusion": self.matriz_confusion,
                "importancia_caracteristicas": self.feature_importance,
            },
            "etl_log": self.etl_log,
        }


def _make_log_entry(
    rule: str,
    description: str,
    affected: int,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "regla": rule,
        "descripcion": description,
        "registros_afectados": int(affected),
    }
    if details:
        entry["detalles"] = details
    return entry


def _resolve_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    if "id_consulta" not in df.columns:
        return df, _make_log_entry(
            "deduplicacion_consultas",
            "No se detectaron columnas para deduplicar.",
            0,
        )

    ordered = df.sort_values(["id_consulta", "fecha"], na_position="last")
    before = len(ordered)
    deduped = ordered.drop_duplicates(subset=["id_consulta"], keep="last")
    removed = before - len(deduped)
    return deduped, _make_log_entry(
        "deduplicacion_consultas",
        "Se conservaron los últimos registros para cada visita única.",
        removed,
    )


def _detect_and_impute_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    missing = int(df.isna().sum().sum())
    if missing == 0:
        return df, _make_log_entry(
            "imputacion_valores_faltantes",
            "No se encontraron valores faltantes.",
            0,
        )

    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        median = df[col].median()
        df[col] = df[col].fillna(median)

    categorical_cols = df.select_dtypes(include=["object"]).columns
    df[categorical_cols] = df[categorical_cols].fillna("Desconocido")

    if "fecha" in df.columns:
        df["fecha"] = df["fecha"].fillna(method="ffill").fillna(method="bfill")

    return df, _make_log_entry(
        "imputacion_valores_faltantes",
        "Valores numéricos imputados con la mediana y categóricos con 'Desconocido'.",
        missing,
        {"columnas_numericas": list(numeric_cols), "columnas_categoricas": list(categorical_cols)},
    )


def _normalize_units(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    conversions: Dict[str, int] = {}

    if "dosis_mg" in df.columns:
        df["dosis_mg"] = pd.to_numeric(df["dosis_mg"], errors="coerce")
        mask_grams = df["dosis_mg"].notna() & (df["dosis_mg"] > 0) & (df["dosis_mg"] < 1)
        if mask_grams.any():
            df.loc[mask_grams, "dosis_mg"] = df.loc[mask_grams, "dosis_mg"] * 1000
            conversions["gramos_a_mg"] = int(mask_grams.sum())

        mask_invalid = df["dosis_mg"].isna() | (df["dosis_mg"] <= 0)
        if mask_invalid.any():
            df.loc[mask_invalid, "dosis_mg"] = pd.NA
            conversions["dosis_invalidas"] = int(mask_invalid.sum())

    if "dosis_mg" in df.columns and "peso_kg" in df.columns:
        safe_weight = df["peso_kg"].replace({0: pd.NA})
        df["dosis_mg_kg"] = (df["dosis_mg"].astype(float)) / safe_weight.astype(float)
        df["dosis_mg_kg"] = df["dosis_mg_kg"].replace({pd.NA: None})

    if "concentracion_mg_ml" in df.columns:
        df["concentracion_mg_ml"] = pd.to_numeric(df["concentracion_mg_ml"], errors="coerce")
        mask_low = df["concentracion_mg_ml"].notna() & (df["concentracion_mg_ml"] > 0) & (
            df["concentracion_mg_ml"] < 1
        )
        if mask_low.any():
            df.loc[mask_low, "concentracion_mg_ml"] = df.loc[mask_low, "concentracion_mg_ml"] * 1000
            conversions["concentracion_g_ml_a_mg_ml"] = int(mask_low.sum())

    details = {k: v for k, v in conversions.items() if v > 0}
    return df, _make_log_entry(
        "normalizacion_unidades",
        "Unidades alineadas a mg, mg/kg y mg/ml.",
        sum(details.values()) if details else 0,
        details or None,
    )


def _correct_weights(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    if "peso_kg" not in df.columns:
        return df, _make_log_entry(
            "correccion_peso",
            "No se encontró columna de peso para corregir.",
            0,
        )

    df["peso_kg"] = pd.to_numeric(df["peso_kg"], errors="coerce")
    valid_weights = df.loc[df["peso_kg"] > 0, "peso_kg"]
    median_weight = float(valid_weights.median()) if not valid_weights.empty else 10.0
    changed_indexes: Set[int] = set()

    mask_zero = df["peso_kg"] <= 0
    if mask_zero.any():
        df.loc[mask_zero, "peso_kg"] = median_weight
        changed_indexes.update(df.index[mask_zero])

    mask_small = df["peso_kg"].between(0.05, 0.5, inclusive="both")
    if mask_small.any():
        df.loc[mask_small, "peso_kg"] = df.loc[mask_small, "peso_kg"] * 10
        changed_indexes.update(df.index[mask_small])

    mask_large = df["peso_kg"] > 120
    if mask_large.any():
        df.loc[mask_large, "peso_kg"] = df.loc[mask_large, "peso_kg"] / 10
        changed_indexes.update(df.index[mask_large])

    return df, _make_log_entry(
        "correccion_peso",
        "Pesos negativos/irreales ajustados con reglas heurísticas clínicas.",
        len(changed_indexes),
        {
            "peso_median_usado": median_weight,
            "ajustes_menores": int(mask_small.sum()),
            "ajustes_mayores": int(mask_large.sum()),
            "reemplazos_no_positivos": int(mask_zero.sum()),
        },
    )


def _filter_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    guardrails: Dict[str, tuple[float, float]] = {
        "dosis_mg": (0.1, 500.0),
        "dosis_mg_kg": (0.05, 40.0),
        "peso_kg": (0.3, 120.0),
        "duracion_dias": (1, 365),
        "valoracion_mejora": (0, 10),
    }

    numeric_df = df.copy()
    for column in guardrails:
        if column in numeric_df.columns:
            numeric_df[column] = pd.to_numeric(numeric_df[column], errors="coerce")

    mask_remove = pd.Series(False, index=df.index)
    details: Dict[str, int] = {}

    for column, (low, high) in guardrails.items():
        if column not in numeric_df.columns:
            continue
        col_mask = numeric_df[column].notna() & ~numeric_df[column].between(low, high)
        if col_mask.any():
            mask_remove = mask_remove | col_mask
            details[column] = int(col_mask.sum())

    removed = int(mask_remove.sum())
    filtered = df.loc[~mask_remove].copy()
    return filtered, _make_log_entry(
        "filtro_outliers",
        "Se eliminaron registros que violan guardrails clínicos.",
        removed,
        {"guardrails": guardrails, "por_columna": details} if details else {"guardrails": guardrails},
    )


def extract_from_postgres() -> pd.DataFrame:
    """Extrae todos los datos desde PostgreSQL y construye un dataset tabular."""
    with SessionLocal() as session:
        consultas_stmt = (
            select(
                Consulta.id_consulta,
                Consulta.fecha,
                Consulta.motivo,
                Consulta.diagnostico,
                Consulta.valoracion_mejora,
                Paciente.id_paciente,
                Paciente.nombre.label("paciente_nombre"),
                Paciente.especie,
                Paciente.sexo,
                Paciente.edad_anios,
                Paciente.peso_kg,
                Veterinario.nombre.label("veterinario_nombre"),
                Veterinario.especialidad.label("veterinario_especialidad"),
                ProductoCBD.nombre_comercial.label("producto_nombre"),
                ProductoCBD.concentracion_mg_ml,
                TratamientoCBD.dosis_mg,
                TratamientoCBD.frecuencia,
                TratamientoCBD.duracion_dias,
            )
            .join(Paciente, Consulta.paciente)
            .join(Veterinario, Consulta.veterinario)
            .join(TratamientoCBD, Consulta.tratamientos)
            .join(ProductoCBD, TratamientoCBD.producto)
        )
        consultas_df = pd.read_sql(consultas_stmt, session.bind)

        parametros_stmt = select(
            ParametroClinico.id_consulta,
            ParametroClinico.nombre_parametro,
            ParametroClinico.valor,
            ParametroClinico.unidad,
        )
        parametros_df = pd.read_sql(parametros_stmt, session.bind)

    if consultas_df.empty:
        return consultas_df

    if parametros_df.empty:
        parametros_pivot = pd.DataFrame({"id_consulta": consultas_df["id_consulta"].unique()})
    else:
        parametros_pivot = (
            parametros_df
            .pivot_table(
                index="id_consulta",
                columns="nombre_parametro",
                values="valor",
                aggfunc="mean",
            )
            .add_prefix("param_")
            .reset_index()
        )

    dataset = consultas_df.merge(parametros_pivot, on="id_consulta", how="left")
    dataset["fecha"] = pd.to_datetime(dataset["fecha"])
    dataset.sort_values("fecha", inplace=True)
    dataset.reset_index(drop=True, inplace=True)
    return dataset


def clean_and_engineer(df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Limpia el dataset, aplica reglas de calidad y genera características útiles."""
    df = df.copy()
    etl_log: List[Dict[str, Any]] = []
    if df.empty:
        return df, etl_log

    df, log_entry = _resolve_duplicates(df)
    etl_log.append(log_entry)

    df, log_entry = _detect_and_impute_missing(df)
    etl_log.append(log_entry)

    df, log_entry = _normalize_units(df)
    etl_log.append(log_entry)

    df, log_entry = _correct_weights(df)
    etl_log.append(log_entry)

    df, log_entry = _filter_outliers(df)
    etl_log.append(log_entry)

    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    if "dosis_mg" in df.columns:
        if "duracion_dias" in df.columns:
            duracion = pd.to_numeric(df["duracion_dias"], errors="coerce").replace({0: 1}).fillna(1)
        else:
            duracion = pd.Series(1, index=df.index, dtype=float)
        df["dosis_diaria"] = df["dosis_mg"].fillna(0) / duracion
    else:
        df["dosis_diaria"] = 0

    df["tratamiento_exitoso"] = df["valoracion_mejora"].apply(
        lambda v: "Sí" if v is not None and v >= 7 else "No"
    )

    return df, etl_log


def build_clustering(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Construye un clustering simple por atributos clave."""
    cols = ["edad_anios", "peso_kg", "dosis_mg", "dosis_diaria"]
    data = df[cols].fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(data)

    n_clusters = min(4, len(df)) if len(df) > 1 else 1
    if n_clusters <= 1:
        return []

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    clusters = model.fit_predict(scaled)

    df_clustered = df.copy()
    df_clustered["cluster"] = clusters

    resumen = []
    for cluster, grupo in df_clustered.groupby("cluster"):
        resumen.append(
            {
                "cluster": int(cluster),
                "conteo": int(len(grupo)),
                "edad_prom": float(grupo["edad_anios"].mean()),
                "peso_prom": float(grupo["peso_kg"].mean()),
                "dosis_prom": float(grupo["dosis_mg"].mean()),
            }
        )

    return resumen


def build_model(df: pd.DataFrame) -> Dict[str, Any]:
    """Entrena un modelo predictivo sencillo sobre el estado de éxito del tratamiento."""
    if df.empty or df["tratamiento_exitoso"].nunique() < 2:
        return {
            "accuracy": 0.0,
            "matriz_confusion": [[0, 0], [0, 0]],
            "feature_importance": [],
        }

    features = df[
        ["edad_anios", "peso_kg", "dosis_mg", "duracion_dias", "dosis_diaria"]
    ].copy()
    target = df["tratamiento_exitoso"].map({"Sí": 1, "No": 0})

    features = features.fillna(features.median())
    target = target.fillna(0)

    if len(target) < 4 or target.nunique() < 2:
        return {
            "accuracy": 0.0,
            "matriz_confusion": [[0, 0], [0, 0]],
            "feature_importance": [],
        }

    stratify_param = target if target.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.3, random_state=42, stratify=stratify_param
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    accuracy = float(accuracy_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred).tolist()

    importance = [
        {"caracteristica": name, "importancia": float(score)}
        for name, score in zip(features.columns, model.feature_importances_)
    ]

    return {
        "accuracy": accuracy,
        "matriz_confusion": cm,
        "feature_importance": importance,
    }


def summarize(df: pd.DataFrame, etl_log: List[Dict[str, Any]]) -> AnalyticsResult:
    if df.empty:
        return AnalyticsResult(
            timestamp=datetime.utcnow(),
            total_consultas=0,
            total_pacientes=0,
            especies={},
            tratamientos_por_especie={},
            clustering_resumen=[],
            modelo_accuracy=0.0,
            matriz_confusion=[[0, 0], [0, 0]],
            feature_importance=[],
            etl_log=etl_log,
        )

    especies_counts = df["especie"].value_counts().to_dict()
    tasas_exito = (
        df.groupby("especie")["tratamiento_exitoso"].apply(lambda x: (x == "Sí").mean() * 100)
        .round(2)
        .to_dict()
    )

    clustering = build_clustering(df)
    modelo = build_model(df)

    return AnalyticsResult(
        timestamp=datetime.utcnow(),
        total_consultas=int(df["id_consulta"].nunique()),
        total_pacientes=int(df["id_paciente"].nunique()),
        especies=especies_counts,
        tratamientos_por_especie=tasas_exito,
        clustering_resumen=clustering,
        modelo_accuracy=modelo["accuracy"],
        matriz_confusion=modelo["matriz_confusion"],
        feature_importance=modelo["feature_importance"],
        etl_log=etl_log,
    )


def write_cache(result: AnalyticsResult) -> None:
    data = result.to_dict()
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def run_once() -> Optional[AnalyticsResult]:
    df = extract_from_postgres()
    if df.empty:
        CACHE_FILE.write_text(
            json.dumps(
                {
                    "generated_at": datetime.utcnow().isoformat(),
                    "totals": {},
                    "etl_log": [],
                }
            )
        )
        return None

    clean_df, etl_log = clean_and_engineer(df)
    result = summarize(clean_df, etl_log)
    write_cache(result)
    return result


def run_forever(interval_seconds: int = 30) -> None:
    while True:
        try:
            result = run_once()
            if result:
                print(f"[{result.timestamp}] Analytics refreshed. Total consultas: {result.total_consultas}")
            else:
                print("[WARN] No hay datos en la base todavía.")
        except Exception as exc:  # pragma: no cover - logging runtime
            print(f"[ERROR] Falló la actualización de analíticas: {exc}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    interval = int(os.getenv("ANALYTICS_REFRESH_SECONDS", "30"))
    run_forever(interval)
