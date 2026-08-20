"""ETL modular: extract → clean → transform → load."""

from datetime import datetime
from typing import Tuple, Dict, Any

import pandas as pd

from database import get_db_session, init_db
from etl.extract import extract_from_view
from etl.clean import validate, clean
from etl.transform import engineer_features, prepare_modeling
from logger import get_logger

logger = get_logger("etl")


class ETLPipeline:
    def __init__(self):
        self.raw_data = None
        self.cleaned_data = None
        self.feature_engineered_data = None
        self.X = None
        self.y = None
        self.feature_names = None
        self.etl_log = []

    def extract_data(self) -> pd.DataFrame:
        session = get_db_session()
        try:
            self.raw_data = extract_from_view(session)
            self._log("Extract", f"{len(self.raw_data)} records")
            return self.raw_data
        finally:
            session.close()

    def validate_data(self) -> Dict[str, Any]:
        result = validate(self.raw_data)
        self._log("Validate", str(result))
        return result

    def clean_data(self) -> pd.DataFrame:
        self.cleaned_data = clean(self.raw_data)
        self._log("Clean", f"{len(self.cleaned_data)} rows")
        return self.cleaned_data

    def transform_data(self) -> pd.DataFrame:
        if self.cleaned_data is None:
            self.cleaned_data = self.raw_data
        return self.cleaned_data

    def engineer_features(self) -> pd.DataFrame:
        self.feature_engineered_data = engineer_features(self.cleaned_data)
        self._log("FeatureEngineering", f"{self.feature_engineered_data.shape[1]} cols")
        return self.feature_engineered_data

    def prepare_for_modeling(self) -> Tuple[pd.DataFrame, pd.Series]:
        self.X, self.y, self.feature_names = prepare_modeling(self.feature_engineered_data)
        self._log("Prepare", f"{len(self.X)} samples, {len(self.feature_names)} features")
        return self.X, self.y

    def run_full_pipeline(self) -> Tuple[pd.DataFrame, pd.Series]:
        init_db()
        self.extract_data()
        self.validate_data()
        self.clean_data()
        self.transform_data()
        self.engineer_features()
        return self.prepare_for_modeling()

    def get_etl_report(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "raw_records": len(self.raw_data) if self.raw_data is not None else 0,
            "cleaned_records": len(self.cleaned_data) if self.cleaned_data is not None else 0,
            "final_records": len(self.X) if self.X is not None else 0,
            "features": len(self.feature_names) if self.feature_names else 0,
            "target_positive": int(self.y.sum()) if self.y is not None else 0,
            "target_negative": int(len(self.y) - self.y.sum()) if self.y is not None else 0,
            "etl_log": self.etl_log,
        }

    def _log(self, step: str, message: str):
        self.etl_log.append({"timestamp": datetime.now().isoformat(), "step": step, "message": message})
