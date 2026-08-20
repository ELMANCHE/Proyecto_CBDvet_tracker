"""
Script para analizar por qué las predicciones siempre salen como 'Bajo potencial'
"""

import joblib
import numpy as np

# Cargar el modelo y los resultados (SIN DATA LEAKAGE)
model = joblib.load('/Users/eliasefrainmanchegonavarro/Documents/Proyecto_CBDvet_tracker/models/random_forest_v20260820_113223.joblib')
results = joblib.load('/Users/eliasefrainmanchegonavarro/Documents/Proyecto_CBDvet_tracker/models/training_results_20260820_113223.joblib')

print("=== ANÁLISIS DEL MODELO ACTUAL ===")
print(f"Feature names: {results.get('feature_names', 'N/A')}")
print(f"\nRandom Forest Results:")
rf_results = results['results']['random_forest']
print(f"Train Accuracy: {rf_results['train_accuracy']:.4f}")
print(f"Test Accuracy: {rf_results['test_accuracy']:.4f}")
print(f"Confusion Matrix: {rf_results['confusion_matrix']}")
print(f"Classification Report:\n{rf_results['classification_report']}")

# Analizar feature importance
print("\n=== FEATURE IMPORTANCE TOP 10 ===")
importances = model.feature_importances_
indices = np.argsort(importances)[::-1][:10]
feature_names = results.get('feature_names', [f'feature_{i}' for i in range(len(importances))])

for i, idx in enumerate(indices):
    print(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")

# Verificar si hay desbalance en las predicciones
print("\n=== ANÁLISIS DE CLASES ===")
conf_matrix = rf_results['confusion_matrix']
print(f"True Negatives (predicción correcta de negativos): {conf_matrix[0][0]}")
print(f"False Positives (predicción incorrecta de positivos): {conf_matrix[0][1]}")
print(f"False Negatives (predicción incorrecta de negativos): {conf_matrix[1][0]}")
print(f"True Positives (predicción correcta de positivos): {conf_matrix[1][1]}")

# Calcular sensibilidad y especificidad
tn, fp, fn, tp = conf_matrix[0][0], conf_matrix[0][1], conf_matrix[1][0], conf_matrix[1][1]
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

print(f"\nSensibilidad (True Positive Rate): {sensitivity:.4f}")
print(f"Especificidad (True Negative Rate): {specificity:.4f}")

# El problema: si la especificidad es muy alta, el modelo tiende a predecir negativos
if specificity > 0.9:
    print("\n⚠️ PROBLEMA IDENTIFICADO: El modelo tiene especificidad muy alta")
    print("   Esto significa que predice 'negativo' (Bajo potencial) casi siempre")
    print("   Necesitamos ajustar el modelo para ser más balanceado")

# PROBLEMA CRÍTICO: nivel_mejora_scaled en features
print("\n=== ✅ VERIFICACIÓN DE DATA LEAKAGE ===")
if 'nivel_mejora_scaled' in results.get('feature_names', []):
    print("⚠️ PROBLEMA: 'nivel_mejora_scaled' está en los features (DATA LEAKAGE)")
else:
    print("✅ CORRECTO: 'nivel_mejora_scaled' NO está en los features (sin data leakage)")

# Recomendaciones para predicciones positivas
print("\n=== RECOMENDACIONES PARA PREDICCIONES POSITIVAS ===")
print("Features más importantes para predicción positiva:")
print("1. severidad_encoded (16.4%) - Usar 'Leve' (0)")
print("2. codigo_paciente_encoded (15.8%) - No controlable")
print("3. consulta_id_scaled (11.7%) - No controlable")
print("4. raza_encoded (9.4%) - No controlable")
print("5. dosis_mg_kg (8.9%) - Usar dosis alta (6-8 mg/kg)")
print("6. frecuencia_encoded (7.9%) - Usar 'Diaria' (1)")
print("7. peso (6.8%) - Peso moderado (10-15 kg)")
print("\nParámetros sugeridos para alta probabilidad positiva:")
print("- severidad: Leve")
print("- dosis_mg_kg: 6.0-8.0")
print("- frecuencia: Diaria")
print("- nivel_estres: 1.0-2.0 (bajo)")
print("- peso_kg: 10.0-15.0")
