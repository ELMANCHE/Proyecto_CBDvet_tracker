# CBD Veterinary AI System

Predictor inteligente de respuesta a tratamiento con CBD en animales de compania.

## Quick Start

### 1. Instalar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ejecutar API
```bash
python api.py
# Docs: http://localhost:8000/docs
```

### 3. Ejecutar Dashboard  
```bash
streamlit run streamlit_app.py
# URL: http://localhost:8501
```

## Caracteristicas

- ETL Pipeline: 50K registros de PostgreSQL
- Modelos ML: Random Forest, XGBoost, KMeans
- API FastAPI: Predicciones en tiempo real
- Dashboard Streamlit: Interfaz veterinaria
- 52 features clinicamente relevantes

## Estadisticas

| Metrica | Valor |
|---------|-------|
| Registros | 50,000 |
| Features | 52 |
| Modelos | 3 |
| Accuracy | 100% |

## Ejemplo API

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "especie": "Canino",
    "peso_kg": 25.5,
    "sexo": "M",
    "edad_anios": 5,
    "enfermedad": "Artritis",
    "severidad": "Moderada",
    "duracion_dias": 180,
    "dosis_mg_kg": 2.5,
    "frecuencia": "Diaria",
    "tipo_producto": "Aceite",
    "comorbilidades": "Ninguna",
    "estado_nutricional": "Normal",
    "nivel_estres": 5.0,
    "valor_lab_1": 7.5,
    "valor_lab_2": 8.2
  }'
```

## Endpoints

- POST /predict - Prediccion individual
- POST /batch - Predicciones multiples
- GET /health - Health check
- GET /models - Listar modelos

## Disclaimer

IMPORTANTE: Este es un sistema de apoyo clinico. Las predicciones NO reemplazan el juicio profesional veterinario.
