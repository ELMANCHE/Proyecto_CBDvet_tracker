"""
Tests unitarios para el módulo de Feature Engineering

Estos tests garantizan que el feature engineering funcione correctamente
y mantenga consistencia entre entrenamiento y predicción.
"""

import pytest
import pandas as pd
from ml.feature_engineering import FeatureEngineer, engineer_patient_features


class TestFeatureEngineer:
    """Tests para la clase FeatureEngineer"""
    
    def test_expected_features_count(self):
        """Verifica que se generen exactamente 29 features (sin data leakage)"""
        patient_data = self._get_sample_patient()
        df = FeatureEngineer.engineer_features(patient_data)
        
        assert df.shape[1] == 29, f"Expected 29 features, got {df.shape[1]}"
    
    def test_expected_features_names(self):
        """Verifica que los nombres de features sean correctos"""
        patient_data = self._get_sample_patient()
        df = FeatureEngineer.engineer_features(patient_data)
        
        assert set(df.columns) == set(FeatureEngineer.EXPECTED_FEATURES), \
            "Feature names don't match expected features"
    
    def test_no_missing_values(self):
        """Verifica que no haya valores nulos"""
        patient_data = self._get_sample_patient()
        df = FeatureEngineer.engineer_features(patient_data)
        
        assert df.isnull().sum().sum() == 0, "DataFrame contains null values"
    
    def test_validate_features_success(self):
        """Verifica que la validación funcione con features correctos"""
        patient_data = self._get_sample_patient()
        df = FeatureEngineer.engineer_features(patient_data)
        
        assert FeatureEngineer.validate_features(df) == True, \
            "Validation should pass for correct features"
    
    def test_validate_features_failure(self):
        """Verifica que la validación falle con features incorrectos"""
        df = pd.DataFrame({"wrong_feature": [1, 2, 3]})
        
        assert FeatureEngineer.validate_features(df) == False, \
            "Validation should fail for incorrect features"
    
    def test_especie_encoding(self):
        """Verifica encoding correcto de especies"""
        test_cases = [
            ("Perro", 0),
            ("Gato", 1),
            ("Canino", 0),
            ("Felino", 1),
            ("Exotico", 2),
        ]
        
        for especie, expected_encoding in test_cases:
            patient_data = self._get_sample_patient()
            patient_data['especie'] = especie
            df = FeatureEngineer.engineer_features(patient_data)
            
            assert df['especie_encoded'].values[0] == expected_encoding, \
                f"Encoding failed for {especie}"
    
    def test_sexo_encoding(self):
        """Verifica encoding correcto de sexo"""
        for sexo, expected_encoding in [("M", 0), ("F", 1)]:
            patient_data = self._get_sample_patient()
            patient_data['sexo'] = sexo
            df = FeatureEngineer.engineer_features(patient_data)
            
            assert df['sexo_encoded'].values[0] == expected_encoding, \
                f"Encoding failed for sexo {sexo}"
    
    def test_grupo_peso_classification(self):
        """Verifica clasificación correcta de grupos de peso"""
        test_cases = [
            (5.0, 1),   # < 10 kg
            (15.0, 2),  # 10-25 kg
            (30.0, 3),  # > 25 kg
        ]
        
        for peso, expected_grupo in test_cases:
            patient_data = self._get_sample_patient()
            patient_data['peso_kg'] = peso
            df = FeatureEngineer.engineer_features(patient_data)
            
            assert df['grupo_peso_num'].values[0] == expected_grupo, \
                f"Grupo peso failed for {peso} kg"
    
    def test_frecuencia_encoding(self):
        """Verifica encoding correcto de frecuencia"""
        for frecuencia, expected_encoding in [("Diaria", 1), ("Cada 2 días", 0)]:
            patient_data = self._get_sample_patient()
            patient_data['frecuencia'] = frecuencia
            df = FeatureEngineer.engineer_features(patient_data)
            
            assert df['frecuencia_encoded'].values[0] == expected_encoding, \
                f"Encoding failed for frecuencia {frecuencia}"
    
    def test_tipo_producto_encoding(self):
        """Verifica encoding correcto de tipo producto"""
        for producto, expected_encoding in [("Aceite", 1), ("Cápsulas", 0)]:
            patient_data = self._get_sample_patient()
            patient_data['tipo_producto'] = producto
            df = FeatureEngineer.engineer_features(patient_data)
            
            assert df['tipo_extracto_encoded'].values[0] == expected_encoding, \
                f"Encoding failed for producto {producto}"
    
    def test_wrapper_function(self):
        """Verifica que la función wrapper funcione correctamente"""
        patient_data = self._get_sample_patient()
        df = engineer_patient_features(patient_data)
        
        assert df.shape[1] == 29, "Wrapper function should generate 29 features (sin data leakage)"
        assert df.isnull().sum().sum() == 0, "Wrapper function should not produce nulls"
    
    def _get_sample_patient(self):
        """Retorna datos de muestra de un paciente"""
        return {
            "especie": "Perro",
            "peso_kg": 10.0,
            "sexo": "M",
            "edad_anios": 5,
            "enfermedad": "Enfermedad Artrosica Grado 5",
            "severidad": "Moderada",
            "duracion_dias": 90,
            "dosis_mg_kg": 2.5,
            "frecuencia": "Diaria",
            "tipo_producto": "Aceite",
            "estado_nutricional": "Normal",
            "nivel_estres": 5.0,
            "cumplimiento": 1.0,
            "alt": 45,
            "ast": 40,
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
