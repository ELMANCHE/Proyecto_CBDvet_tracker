"""Tests ETL."""

import pandas as pd
import pytest
from etl.clean import validate, clean
from etl.transform import engineer_features, prepare_modeling


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "consulta_id": [1, 2, 3],
        "peso_kg": [10.0, 25.0, 0.0],
        "edad_anios": [3, 5, -1],
        "dosis_mg_kg": [2.5, 3.0, 600],
        "nivel_mejora": [8, 7, 6],
        "respuesta": ["Exitoso", "Exitoso", "Parcial"],
        "especie": ["Perro", "Gato", "Perro"],
        "enfermedad": ["Artritis", "Ansiedad", "Dolor"],
    })


def test_validate_detects_anomalies(sample_df):
    issues = validate(sample_df)
    assert issues["weight_anomalies"] >= 1
    assert issues["dosis_anomalies"] >= 1


def test_clean_removes_invalid_weight(sample_df):
    cleaned = clean(sample_df)
    assert (cleaned["peso_kg"] > 0).all()


def test_engineer_features_creates_target(sample_df):
    cleaned = clean(sample_df)
    featured = engineer_features(cleaned)
    assert "target" in featured.columns


def test_prepare_modeling_returns_xy(sample_df):
    featured = engineer_features(clean(sample_df))
    X, y, names = prepare_modeling(featured)
    assert len(X) == len(y)
    assert len(names) > 0
