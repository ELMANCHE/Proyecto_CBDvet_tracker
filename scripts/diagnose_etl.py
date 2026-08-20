"""Script para diagnosticar el balanceo de clases en el ETL."""

from etl import ETLPipeline
from etl.transform import prepare_modeling
import pandas as pd

def diagnose_etl():
    """Diagnóstico completo del ETL"""
    print("=" * 60)
    print("DIAGNÓSTICO ETL - BALANCEO DE CLASES")
    print("=" * 60)
    
    # Ejecutar pipeline
    pipeline = ETLPipeline()
    pipeline.extract_data()
    pipeline.validate_data()
    pipeline.clean_data()
    pipeline.transform_data()
    df_engineered = pipeline.engineer_features()
    
    print(f"\n📊 Datos después de feature engineering:")
    print(f"   Total registros: {len(df_engineered)}")
    print(f"   Columnas: {df_engineered.shape[1]}")
    
    # Ver distribución de nivel_mejora
    if "nivel_mejora" in df_engineered.columns:
        print(f"\n📈 Distribución nivel_mejora:")
        print(df_engineered["nivel_mejora"].value_counts().sort_index())
    
    # Ver distribución del target
    if "target" in df_engineered.columns:
        print(f"\n🎯 Distribución TARGET (antes de prepare_modeling):")
        print(df_engineered["target"].value_counts())
        pos = (df_engineered["target"] == 1).sum()
        neg = (df_engineered["target"] == 0).sum()
        ratio = pos / neg if neg > 0 else 0
        print(f"   Ratio pos/neg: {ratio:.2f}")
    
    # Preparar para modelado SIN balanceo
    print(f"\n🔧 prepare_modeling SIN balanceo:")
    X_no_balance, y_no_balance, features = prepare_modeling(df_engineered, balance=False)
    print(f"   X shape: {X_no_balance.shape}")
    print(f"   y shape: {y_no_balance.shape}")
    print(f"   Clases: {y_no_balance.value_counts().to_dict()}")
    pos = (y_no_balance == 1).sum()
    neg = (y_no_balance == 0).sum()
    ratio = pos / neg if neg > 0 else 0
    print(f"   Ratio pos/neg: {ratio:.2f}")
    
    # Preparar para modelado CON balanceo
    print(f"\n🔧 prepare_modeling CON balanceo:")
    X_balanced, y_balanced, features = prepare_modeling(df_engineered, balance=True)
    print(f"   X shape: {X_balanced.shape}")
    print(f"   y shape: {y_balanced.shape}")
    print(f"   Clases: {y_balanced.value_counts().to_dict()}")
    pos = (y_balanced == 1).sum()
    neg = (y_balanced == 0).sum()
    ratio = pos / neg if neg > 0 else 0
    print(f"   Ratio pos/neg: {ratio:.2f}")
    
    # Verificar si hay valores únicos
    print(f"\n🔍 Valores únicos en y:")
    print(f"   Únicos: {y_balanced.unique()}")
    print(f"   ¿Solo clase 0?: {(y_balanced == 0).all()}")
    print(f"   ¿Solo clase 1?: {(y_balanced == 1).all()}")

if __name__ == "__main__":
    diagnose_etl()
