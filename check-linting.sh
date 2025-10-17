#!/bin/bash
# Script para probar el linter localmente antes de commit
# Uso: bash check-linting.sh

echo "🧪 Ejecutando verificaciones de linting (igual que CI/CD)..."
echo "=================================================="

# Asegurar que los contenedores están ejecutándose
echo "🔄 Iniciando contenedores..."
docker compose up -d

# Instalar herramientas si no están instaladas
echo "🔧 Instalando herramientas de linting..."
docker compose exec web pip install flake8 black isort --quiet

echo ""
echo "🧪 1. Verificando errores críticos con flake8..."
if docker compose exec web /home/app/.local/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,.git; then
    echo "✅ flake8: Sin errores críticos"
else
    echo "❌ flake8: Errores encontrados"
    exit 1
fi

echo ""
echo "🧪 2. Verificando ordenamiento de imports con isort..."
if docker compose exec web /home/app/.local/bin/isort . --check-only --diff --profile black --skip=venv; then
    echo "✅ isort: Imports correctamente ordenados"
else
    echo "❌ isort: Imports mal ordenados"
    echo "💡 Para arreglar: docker compose exec web /home/app/.local/bin/isort . --profile black --skip=venv"
    exit 1
fi

echo ""
echo "🧪 3. Verificando formateo con black..."
if docker compose exec web /home/app/.local/bin/black . --check --exclude="venv"; then
    echo "✅ black: Código correctamente formateado"
else
    echo "❌ black: Código mal formateado"
    echo "💡 Para arreglar: docker compose exec web /home/app/.local/bin/black . --exclude='venv'"
    exit 1
fi

echo ""
echo "🎉 ¡Todas las verificaciones pasaron!"
echo "✅ Tu código pasará el pipeline CI/CD"