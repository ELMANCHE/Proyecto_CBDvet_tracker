"""
Configuration management for the CBD Veterinary AI System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    MODELS_DIR = PROJECT_ROOT / "models"
    REPORTS_DIR = PROJECT_ROOT / "reports"
    
    # Create directories if they don't exist
    for dir_path in [DATA_DIR, LOGS_DIR, MODELS_DIR, REPORTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Database configuration
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "cbdanalisis")
    DATABASE_USER = os.getenv("DATABASE_USER", "admin")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "admin")
    
    # Build PostgreSQL URL
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
        f"{DATABASE_HOST}:{DATABASE_PORT}/"
        f"{DATABASE_NAME}"
    )
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ML Configuration
    RANDOM_STATE = int(os.getenv("RANDOM_STATE", 42))
    TEST_SIZE = float(os.getenv("TEST_SIZE", 0.25))  # Aumentado a 0.25 para más datos de entrenamiento
    CV_FOLDS = int(os.getenv("CV_FOLDS", 10))  # Aumentado a 10 para validación más robusta
    
    # Model parameters - optimizados extremadamente para evitar overfitting
    RF_N_ESTIMATORS = 20  # Reducido drásticamente para evitar overfitting
    RF_MAX_DEPTH = 4  # Reducido drásticamente para evitar overfitting
    RF_MIN_SAMPLES_SPLIT = 20  # Aumentado significativamente para regularización
    RF_MIN_SAMPLES_LEAF = 10  # Aumentado significativamente para regularización
    RF_MAX_FEATURES = "log2"  # Más restrictivo que sqrt
    XGB_N_ESTIMATORS = 50  # Reducido drásticamente
    XGB_MAX_DEPTH = 3  # Reducido drásticamente
    XGB_LEARNING_RATE = 0.05  # Reducido para más regularización
    XGB_SUBSAMPLE = 0.6  # Más agresivo
    XGB_COLSAMPLE_BYTREE = 0.6  # Más agresivo
    KMEANS_N_CLUSTERS = 4


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"


def get_config() -> Config:
    """Get the appropriate configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# Export configuration instance
config = get_config()
