"""Script para probar el feature engineering y ver el desajuste."""

import pandas as pd
from datetime import datetime

def engineer_features_test():
    nut = {"Bajo": 0, "Normal": 1, "Sobrepeso": 2, "Obeso": 3}
    esp = {"Canino": 0, "Felino": 1, "Exotico": 2, "Perro": 0, "Gato": 1}
    sev = {"Leve": 0, "Moderada": 1, "Grave": 2}
    now = datetime.now()
    
    # Simular paciente
    data = {
        "edad_anios": 5, "peso_kg": 10.0,
        "duracion_dias": 90, "dosis_mg_kg": 2.5,
        "frecuencia": 1,  # Diaria
        "estado_nutricional": 1,  # Normal
        "alt": 45, "ast": 40,
        "nivel_estres": 5.0, "cumplimiento": 1.0,
        "mes": now.month, "dia_semana": now.weekday(),
        "sexo_encoded": 0,  # M
        "especie_encoded": 0,  # Canino
        "severidad_encoded": 1,  # Moderada
        "enfermedad_encoded": 7,  # hash
    }
    
    df = pd.DataFrame([data])
    print("FEATURES GENERADOS POR API:")
    print(f"  Total: {len(df.columns)}")
    print(f"  Features: {list(df.columns)}")
    
    # Features que espera el preprocesador
    expected_features = ['consulta_id', 'peso', 'nivel_estres', 'alt', 'ast', 'dosis_mg_kg', 'peso_kg', 
                         'consulta_id_scaled', 'peso_scaled', 'nivel_estres_scaled', 'alt_scaled', 'ast_scaled', 
                         'dosis_mg_kg_scaled', 'nivel_mejora_scaled', 'peso_kg_scaled', 'mes', 'dia_semana', 
                         'es_fin_semana', 'grupo_peso_num', 'codigo_paciente_encoded', 'especie_encoded', 
                         'raza_encoded', 'sexo_encoded', 'enfermedad_encoded', 'severidad_encoded', 
                         'actividad_fisica_encoded', 'apetito_encoded', 'frecuencia_encoded', 
                         'tipo_extracto_encoded', 'respuesta_encoded']
    
    print(f"\nFEATURES ESPERADOS POR PREPROCESADOR:")
    print(f"  Total: {len(expected_features)}")
    
    missing = [f for f in expected_features if f not in df.columns]
    print(f"\nFEATURES FALTANTES ({len(missing)}):")
    for f in missing:
        print(f"  - {f}")
    
    extra = [f for f in df.columns if f not in expected_features]
    print(f"\nFEATURES EXTRA ({len(extra)}):")
    for f in extra:
        print(f"  - {f}")

if __name__ == "__main__":
    engineer_features_test()
