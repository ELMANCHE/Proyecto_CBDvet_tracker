"""SHAP explicabilidad para predicciones."""

from typing import Dict, List, Any, Optional
import numpy as np

from logger import get_logger

logger = get_logger("ml.shap")

SHAP_AVAILABLE = False
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    pass


def explain_prediction(model, X: np.ndarray, feature_names: List[str], top_n: int = 10) -> Dict[str, Any]:
    """Retorna explicación SHAP o fallback a feature importances."""
    if SHAP_AVAILABLE and hasattr(model, "predict_proba"):
        try:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) > 1 else sv[0]
            values = sv[0] if sv.ndim > 1 else sv
            pairs = sorted(zip(feature_names, values), key=lambda x: abs(x[1]), reverse=True)[:top_n]
            return {
                "method": "shap",
                "features": [{"name": n, "contribution": float(v)} for n, v in pairs],
            }
        except Exception as e:
            logger.warning(f"SHAP failed: {e}")

    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)[:top_n]
        return {
            "method": "feature_importance",
            "features": [{"name": n, "contribution": float(v)} for n, v in pairs],
        }

    return {"method": "none", "features": []}
