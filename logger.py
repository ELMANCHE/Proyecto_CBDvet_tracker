"""
Logging configuration for the CBD Veterinary AI System
"""

import logging
import logging.config
from pathlib import Path
from config import config

# Create logs directory
config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": config.LOG_LEVEL,
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": config.LOG_LEVEL,
            "formatter": "detailed",
            "filename": config.LOGS_DIR / "cbd_system.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "file_etl": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": config.LOGS_DIR / "etl.log",
            "maxBytes": 10485760,
            "backupCount": 3
        },
        "file_training": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": config.LOGS_DIR / "training.log",
            "maxBytes": 10485760,
            "backupCount": 3
        },
    },
    "loggers": {
        "": {  # root logger
            "level": config.LOG_LEVEL,
            "handlers": ["console", "file"]
        },
        "etl": {
            "level": "DEBUG",
            "handlers": ["console", "file_etl"],
            "propagate": False
        },
        "training": {
            "level": "DEBUG",
            "handlers": ["console", "file_training"],
            "propagate": False
        },
    }
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
