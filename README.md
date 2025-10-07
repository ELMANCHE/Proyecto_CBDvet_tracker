# Proyecto CBDVet Tracker

Aplicación web para registrar casos clínicos veterinarios tratados con CBD y analizarlos mediante dashboards interactivos.

## Componentes principales

- **Flask**: formulario web para captura de datos clínicos y persistencia en PostgreSQL.
- **PostgreSQL**: base de datos relacional que almacena propietarios, pacientes, consultas, parámetros y tratamientos.
- **Streamlit**: tablero de análisis y exploración de resultados.

## Requisitos previos

- Docker y Docker Compose instalados.
- Archivo `.env` basado en `.env.example` con las credenciales deseadas.

```bash
cp .env.example .env
# Opcional: editar el archivo para personalizar contraseñas y secretos
```

## Inicio rápido con Docker

Sigue estos pasos para dejar la aplicación corriendo desde cero:

```bash
# 1. (Opcional) crea un clon local
git clone https://github.com/ELMANCHE/Proyecto_CBDvet_tracker.git
cd Proyecto_CBDvet_tracker

# 2. Configura variables de entorno (puedes editarlas después)
cp .env.example .env

# 3. Construye las imágenes y levanta los servicios necesarios
docker compose up --build -d web db

# 4. (Opcional) comprueba el estado de los contenedores
docker compose ps

# 5. Accede al formulario Flask
#    http://localhost:5001

# 6. (Opcional) revisa logs recientes del backend
docker compose logs --tail=50 web

# 7. (Opcional) ingresa a PostgreSQL para verificar datos
docker compose exec db psql -U "${POSTGRES_USER:-cbdvet_user}" -d "${POSTGRES_DB:-cbdvet_db}"

# 8. Para apagar y limpiar (incluyendo la base de datos generada en el volumen)
docker compose down -v
```

> Nota: en la configuración actual el formulario Flask queda disponible en `http://localhost:5001` y la base de datos se expone en el puerto `5434` del host.

## Desarrollo local sin Docker (opcional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000
```

## Estructura de la base de datos

El modelo relacional incluye las tablas `Propietario`, `Paciente`, `Veterinario`, `Consulta`, `ParametroClinico`, `ProductoCBD` y `TratamientoCBD`, alineadas con el esquema definido en el proyecto.