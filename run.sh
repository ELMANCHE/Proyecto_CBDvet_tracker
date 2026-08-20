#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# QUICK START GUIDE - CBD Veterinary AI System
# ═══════════════════════════════════════════════════════════════════════════════
# 
# Ejecuta este script para lanzar el sistema completo
# o sigue los pasos individualmente según necesites
#
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🐾 CBD Veterinary AI System"
echo "══════════════════════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: Verificar Prerequisites
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "📋 Paso 1: Verificando prerequisites..."

# Verificar Python
if ! command -v python &> /dev/null; then
    echo "❌ Python no instalado"
    exit 1
fi
echo "✅ Python: $(python --version)"

# Verificar PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL no instalado"
    exit 1
fi
echo "✅ PostgreSQL disponible"

# Verificar venv
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment no encontrado"
    echo "   Créalo con: python -m venv .venv"
    exit 1
fi
echo "✅ Virtual environment existe"

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Activar Virtual Environment
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "🔄 Paso 2: Activando virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activado"

# ─────────────────────────────────────────────────────────────────────────────
# PASO 3: Verificar BD
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "🗄️  Paso 3: Verificando base de datos PostgreSQL..."

DB_CHECK=$(PGPASSWORD=admin psql -h localhost -U postgres -d cbdanalisis -c "SELECT COUNT(*) FROM paciente LIMIT 1;" 2>&1)

if [[ $DB_CHECK == *"5000"* ]] || [[ $DB_CHECK == *"count"* ]]; then
    echo "✅ Base de datos conectada (5000 registros en paciente)"
else
    echo "⚠️  No se pudo conectar a BD"
    echo "   User: postgres"
    echo "   Host: localhost"
    echo "   Database: cbdanalisis"
fi

# ─────────────────────────────────────────────────────────────────────────────
# PASO 4: Menu de opciones
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo "🎯 Elige qué ejecutar:"
echo "──────────────────────────────────────────────────────────────────────────"
echo ""
echo "1️⃣  - Ejecutar Pipeline Completo (ETL → Training → Reports)"
echo "2️⃣  - Lanzar API (http://localhost:8000)"
echo "3️⃣  - Lanzar Dashboard (http://localhost:8501)"
echo "4️⃣  - Ejecutar TODO: API + Dashboard (en paralelo)"
echo "5️⃣  - Ver logs del último run"
echo "6️⃣  - Ver resultados (Reports JSON)"
echo "0️⃣  - Salir"
echo ""

read -p "Selecciona opción (0-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Ejecutando Pipeline Completo..."
        echo "──────────────────────────────────────────────────────────────────────────"
        python main.py
        echo ""
        echo "✅ Pipeline completado"
        echo "📊 Revisa los reportes en: reports/"
        ;;
    2)
        echo ""
        echo "🚀 Lanzando API FastAPI..."
        echo "──────────────────────────────────────────────────────────────────────────"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo "🔗 API URL: http://localhost:8000"
        echo ""
        echo "Presiona Ctrl+C para detener la API"
        echo ""
        python api.py
        ;;
    3)
        echo ""
        echo "🚀 Lanzando Dashboard Streamlit..."
        echo "──────────────────────────────────────────────────────────────────────────"
        echo "🎨 Dashboard: http://localhost:8501"
        echo ""
        echo "Presiona Ctrl+C para detener el dashboard"
        echo ""
        streamlit run streamlit_app.py
        ;;
    4)
        echo ""
        echo "🚀 Lanzando API + Dashboard en paralelo..."
        echo "──────────────────────────────────────────────────────────────────────────"
        echo ""
        echo "📚 API Docs: http://localhost:8000/docs"
        echo "🎨 Dashboard: http://localhost:8501"
        echo ""
        
        # Lanzar API en background
        echo "📌 Iniciando API en background..."
        python api.py &
        API_PID=$!
        echo "✅ API PID: $API_PID"
        
        # Esperar un momento para que API inicie
        sleep 3
        
        # Lanzar Dashboard
        echo "📌 Iniciando Dashboard..."
        streamlit run streamlit_app.py
        
        # Al salir del dashboard, terminar API
        kill $API_PID
        ;;
    5)
        echo ""
        echo "📋 Últimas líneas del log:"
        echo "──────────────────────────────────────────────────────────────────────────"
        tail -50 logs/cbd_system.log
        ;;
    6)
        echo ""
        echo "📊 Reportes disponibles:"
        echo "──────────────────────────────────────────────────────────────────────────"
        ls -lah reports/*.json | tail -5
        echo ""
        echo "📖 Ver reporte final:"
        echo "cat reports/$(ls -t reports/final_report_*.json | head -1) | python -m json.tool | head -50"
        ;;
    0)
        echo "👋 Hasta pronto!"
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "✅ Completo!"
