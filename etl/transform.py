"""Transformación y feature engineering."""

import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek

from logger import get_logger

logger = get_logger("etl.transform")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Excluir nivel_mejora de scaled features para evitar DATA LEAKAGE
    exclude_cols = ['nivel_mejora', 'target']
    for col in out.select_dtypes(include=[np.number]).columns:
        if col not in exclude_cols:
            cmin, cmax = out[col].min(), out[col].max()
            out[f"{col}_scaled"] = (out[col] - cmin) / (cmax - cmin) if cmax > cmin else 0
    return out


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = transform(df)

    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")
        out["mes"] = out["fecha"].dt.month
        out["dia_semana"] = out["fecha"].dt.dayofweek
        out["es_fin_semana"] = out["dia_semana"].isin([5, 6]).astype(int)

    edad_col = "edad_anios" if "edad_anios" in out.columns else None
    if edad_col:
        out["grupo_edad_num"] = pd.cut(
            out[edad_col], bins=[-1, 1, 3, 8, 15, 30], labels=False
        ).fillna(1).astype(int)

    peso_col = "peso_kg" if "peso_kg" in out.columns else "peso"
    if peso_col in out.columns:
        out["grupo_peso_num"] = pd.cut(
            out[peso_col], bins=[0, 5, 15, 50, 150], labels=False
        ).fillna(1).astype(int)

    for col in out.select_dtypes(include=["object"]).columns:
        if col != "fecha":
            out[f"{col}_encoded"] = pd.factorize(out[col].astype(str))[0]

    # Priorizar nivel_mejora para el target, ya que es más confiable que respuesta
    if "nivel_mejora" in out.columns and out["nivel_mejora"].notna().any():
        out["target"] = (out["nivel_mejora"] >= 7).astype(int)
    elif "respuesta" in out.columns:
        out["target"] = (out["respuesta"].astype(str).str.lower() == "exitoso").astype(int)

    logger.info(f"Features engineered: {out.shape[1]} columns")
    return out


def prepare_modeling(df: pd.DataFrame, balance: bool = True):
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    features = [c for c in numeric if c not in ("target", "nivel_mejora")]
    X = df[features].fillna(0).replace([np.inf, -np.inf], 0)
    y = df["target"] if "target" in df.columns else (df["nivel_mejora"] >= 7).astype(int)
    mask = y.notna()
    X, y = X[mask], y[mask]
    
    # Balanceo de clases si está activado
    if balance and len(y) > 10:
        pos_count = (y == 1).sum()
        neg_count = (y == 0).sum()
        ratio = pos_count / neg_count if neg_count > 0 else 0
        
        logger.info(f"Clases antes de balanceo: Pos={pos_count}, Neg={neg_count}, Ratio={ratio:.2f}")
        
        # Si ratio < 0.7 o > 1.3, aplicar balanceo (más agresivo)
        if ratio < 0.7 or ratio > 1.3:
            try:
                # Usar SMOTE para oversampling de la clase minoritaria
                k_neighbors = min(5, min(pos_count, neg_count) - 1)
                if k_neighbors < 1:
                    k_neighbors = 1
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_resampled, y_resampled = smote.fit_resample(X, y)
                
                new_pos = (y_resampled == 1).sum()
                new_neg = (y_resampled == 0).sum()
                new_ratio = new_pos / new_neg if new_neg > 0 else 0
                
                logger.info(f"Clases después de SMOTE: Pos={new_pos}, Neg={new_neg}, Ratio={new_ratio:.2f}")
                X = pd.DataFrame(X_resampled, columns=X.columns)
                y = pd.Series(y_resampled)
                
            except Exception as e:
                logger.warning(f"SMOTE falló ({e}), usando datos sin balanceo")
    
    return X, y, features
