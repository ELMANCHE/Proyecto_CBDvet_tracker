"""Sklearn preprocessing pipeline."""

import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import config
from logger import get_logger

logger = get_logger("ml.pipeline")


def build_preprocessor(feature_names: list) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])


def fit_preprocessor(X: pd.DataFrame) -> tuple:
    preprocessor = build_preprocessor(X.columns.tolist())
    X_transformed = preprocessor.fit_transform(X)
    return preprocessor, pd.DataFrame(X_transformed, columns=X.columns)


def save_artifacts(preprocessor, feature_names: list, dataset_version: str) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {}
    pre_path = config.MODELS_DIR / f"preprocessor_v{ts}.joblib"
    joblib.dump(preprocessor, pre_path)
    paths["preprocessor"] = str(pre_path)

    meta_path = config.MODELS_DIR / f"dataset_meta_v{ts}.joblib"
    joblib.dump({"feature_names": feature_names, "dataset_version": dataset_version, "timestamp": ts}, meta_path)
    paths["dataset_meta"] = str(meta_path)
    logger.info(f"Saved preprocessor and metadata: {ts}")
    return paths


def load_latest_preprocessor():
    files = sorted(config.MODELS_DIR.glob("preprocessor_v*.joblib"))
    meta_files = sorted(config.MODELS_DIR.glob("dataset_meta_v*.joblib"))
    if not files:
        return None, None
    pre = joblib.load(files[-1])
    meta = joblib.load(meta_files[-1]) if meta_files else {}
    return pre, meta
