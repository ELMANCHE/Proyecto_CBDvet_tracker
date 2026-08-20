"""
Módulo independiente de Feature Engineering para CBD Veterinary System

Este módulo centraliza la lógica de feature engineering para garantizar
consistencia entre entrenamiento y predicción en producción.
"""

from datetime import datetime
from typing import Dict, Any
import pandas as pd


class FeatureEngineer:
    """Clase para generar features consistentes para el modelo ML"""
    
    # Mapeos de variables categóricas
    NUTRICION_MAP = {"Bajo": 0, "Normal": 1, "Sobrepeso": 2, "Obeso": 3}
    ESPECIE_MAP = {"Canino": 0, "Felino": 1, "Exotico": 2, "Perro": 0, "Gato": 1}
    SEVERIDAD_MAP = {"Leve": 0, "Moderada": 1, "Grave": 2}
    
    # Features que espera el preprocesador (SIN DATA LEAKAGE)
    EXPECTED_FEATURES = [
        'consulta_id', 'peso', 'nivel_estres', 'alt', 'ast', 'dosis_mg_kg', 'peso_kg',
        'consulta_id_scaled', 'peso_scaled', 'nivel_estres_scaled', 'alt_scaled', 'ast_scaled',
        'dosis_mg_kg_scaled', 'peso_kg_scaled',  # Eliminado nivel_mejora_scaled (DATA LEAKAGE)
        'mes', 'dia_semana', 'es_fin_semana', 'grupo_peso_num',
        'codigo_paciente_encoded', 'especie_encoded', 'raza_encoded',
        'sexo_encoded', 'enfermedad_encoded', 'severidad_encoded',
        'actividad_fisica_encoded', 'apetito_encoded', 'frecuencia_encoded',
        'tipo_extracto_encoded', 'respuesta_encoded'
    ]
    
    @classmethod
    def engineer_features(cls, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Genera features para un paciente individual
        
        Args:
            patient_data: Diccionario con datos del paciente
            
        Returns:
            DataFrame con los 30 features esperados por el preprocesador
        """
        now = datetime.now()
        
        # Extraer valores con defaults
        peso_kg = patient_data.get('peso_kg', 10.0)
        nivel_estres = patient_data.get('nivel_estres', 5.0)
        alt = patient_data.get('alt', 45)
        ast = patient_data.get('ast', 40)
        dosis_mg_kg = patient_data.get('dosis_mg_kg', 2.5)
        especie = patient_data.get('especie', 'Perro')
        sexo = patient_data.get('sexo', 'M')
        severidad = patient_data.get('severidad', 'Moderada')
        enfermedad = patient_data.get('enfermedad', '')
        frecuencia = patient_data.get('frecuencia', 'Diaria')
        tipo_producto = patient_data.get('tipo_producto', 'Aceite')
        
        # Generar todos los features
        data = {
            "consulta_id": 0,  # Placeholder para nuevos pacientes
            "peso": peso_kg,
            "nivel_estres": nivel_estres,
            "alt": alt,
            "ast": ast,
            "dosis_mg_kg": dosis_mg_kg,
            "peso_kg": peso_kg,  # Mantenido por compatibilidad
            "consulta_id_scaled": 0,
            "peso_scaled": 0,
            "nivel_estres_scaled": 0,
            "alt_scaled": 0,
            "ast_scaled": 0,
            "dosis_mg_kg_scaled": 0,
            # Eliminado nivel_mejora_scaled (DATA LEAKAGE)
            "peso_kg_scaled": 0,
            "mes": now.month,
            "dia_semana": now.weekday(),
            "es_fin_semana": 1 if now.weekday() >= 5 else 0,
            "grupo_peso_num": cls._get_grupo_peso(peso_kg),
            "codigo_paciente_encoded": 0,
            "especie_encoded": cls.ESPECIE_MAP.get(especie, 0),
            "raza_encoded": 0,
            "sexo_encoded": 0 if sexo == "M" else 1,
            "enfermedad_encoded": hash(enfermedad) % 10,
            "severidad_encoded": cls.SEVERIDAD_MAP.get(severidad, 1),
            "actividad_fisica_encoded": 1,
            "apetito_encoded": 1,
            "frecuencia_encoded": 1 if "Diaria" in frecuencia else 0,
            "tipo_extracto_encoded": 1 if "Aceite" in tipo_producto else 0,
            "respuesta_encoded": 0,
        }
        
        df = pd.DataFrame([data])
        
        # Asegurar que tenga todos los features esperados
        for feature in cls.EXPECTED_FEATURES:
            if feature not in df.columns:
                df[feature] = 0
        
        # Ordenar según features esperados
        df = df[cls.EXPECTED_FEATURES]
        
        return df.fillna(0)
    
    @classmethod
    def _get_grupo_peso(cls, peso_kg: float) -> int:
        """Clasifica el peso en grupos"""
        if peso_kg < 10:
            return 1
        elif peso_kg < 25:
            return 2
        else:
            return 3
    
    @classmethod
    def validate_features(cls, df: pd.DataFrame) -> bool:
        """
        Valida que el DataFrame tenga los features correctos
        
        Args:
            df: DataFrame a validar
            
        Returns:
            True si tiene los features correctos, False otherwise
        """
        missing = set(cls.EXPECTED_FEATURES) - set(df.columns)
        extra = set(df.columns) - set(cls.EXPECTED_FEATURES)
        
        if missing:
            print(f"❌ Features faltantes: {missing}")
        if extra:
            print(f"⚠️  Features extra: {extra}")
            
        return len(missing) == 0


# Función de conveniencia para uso en API
def engineer_patient_features(patient_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Función wrapper para feature engineering
    
    Args:
        patient_data: Diccionario con datos del paciente
        
    Returns:
        DataFrame con features procesados
    """
    return FeatureEngineer.engineer_features(patient_data)
