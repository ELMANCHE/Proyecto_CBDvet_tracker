"""Script para verificar carga del modelo y preprocesador."""

import joblib
import os
from config import config

def test_model_loading():
    models_dir = config.MODELS_DIR
    
    # Listar archivos de modelos
    print("ARCHIVOS EN MODELS_DIR:")
    for f in os.listdir(models_dir):
        print(f"  {f}")
    
    # Cargar modelo más reciente
    model_files = [f for f in os.listdir(models_dir) if f.startswith('random_forest_')]
    if model_files:
        latest_model = sorted(model_files)[-1]
        print(f"\nCargando modelo: {latest_model}")
        model = joblib.load(os.path.join(models_dir, latest_model))
        print(f"Modelo cargado: {type(model)}")
        print(f"Features esperados: {model.n_features_in_ if hasattr(model, 'n_features_in_') else 'N/A'}")
    
    # Cargar preprocesador más reciente
    preproc_files = [f for f in os.listdir(models_dir) if f.startswith('preprocessor_')]
    if preproc_files:
        latest_preproc = sorted(preproc_files)[-1]
        print(f"\nCargando preprocesador: {latest_preproc}")
        preproc = joblib.load(os.path.join(models_dir, latest_preproc))
        print(f"Preprocesador cargado: {type(preproc)}")
        if hasattr(preproc, 'feature_names_in_'):
            print(f"Features del preprocesador: {preproc.feature_names_in_}")

if __name__ == "__main__":
    test_model_loading()
