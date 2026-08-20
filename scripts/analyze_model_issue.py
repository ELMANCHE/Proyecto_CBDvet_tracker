"""Script para analizar el problema del modelo que siempre predice lo mismo."""

import joblib
import os
from config import config
import pandas as pd
import numpy as np

def analyze_model():
    models_dir = config.MODELS_DIR
    
    # Cargar modelo más reciente
    model_files = [f for f in os.listdir(models_dir) if f.startswith('random_forest_')]
    latest_model = sorted(model_files)[-1]
    model = joblib.load(os.path.join(models_dir, latest_model))
    
    print(f"MODELO: {latest_model}")
    print(f"Tipo: {type(model)}")
    print(f"Estimadores: {model.n_estimators}")
    print(f"Max depth: {model.max_depth}")
    print(f"Features esperados: {model.n_features_in_}")
    
    # Verificar feature importance
    if hasattr(model, 'feature_importances_'):
        print(f"\nFEATURE IMPORTANCE TOP 10:")
        indices = np.argsort(model.feature_importances_)[::-1][:10]
        for i, idx in enumerate(indices):
            print(f"  {i+1}. Feature {idx}: {model.feature_importances_[idx]:.4f}")
    
    # Cargar preprocesador más reciente
    preproc_files = [f for f in os.listdir(models_dir) if f.startswith('preprocessor_')]
    latest_preproc = sorted(preproc_files)[-1]
    preproc = joblib.load(os.path.join(models_dir, latest_preproc))
    
    print(f"\nPREPROCESADOR: {latest_preproc}")
    print(f"Tipo: {type(preproc)}")
    
    if hasattr(preproc, 'feature_names_in_'):
        print(f"Features del preprocesador: {len(preproc.feature_names_in_)}")
        print(f"Features: {list(preproc.feature_names_in_)}")
    
    # Cargar metadata del dataset
    meta_files = [f for f in os.listdir(models_dir) if f.startswith('dataset_meta_')]
    if meta_files:
        latest_meta = sorted(meta_files)[-1]
        meta = joblib.load(os.path.join(models_dir, latest_meta))
        print(f"\nMETADATA: {latest_meta}")
        print(f"Target distribution: {meta.get('target_distribution', 'N/A')}")
        print(f"Feature count: {meta.get('feature_count', 'N/A')}")
        print(f"Sample count: {meta.get('sample_count', 'N/A')}")

if __name__ == "__main__":
    analyze_model()
