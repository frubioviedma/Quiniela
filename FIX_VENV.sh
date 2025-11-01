#!/bin/bash

# Fix para venv en Python 3.13

echo "=========================================="
echo "FIX de entorno virtual para Python 3.13"
echo "=========================================="

# Desactivar venv actual si existe
deactivate 2>/dev/null || true

# Eliminar venv corrupto
if [ -d "env" ]; then
    echo "Eliminando venv anterior..."
    rm -rf env
fi

# Instalar python3-full
echo "Instalando python3-full..."
sudo apt update
sudo apt install -y python3-full

# Crear nuevo venv
echo "Creando nuevo entorno virtual..."
python3 -m venv env

# Activar
echo "Activando entorno virtual..."
source env/bin/activate

# Verificar que funciona
echo "Verificando pip..."
which pip
pip --version

# Instalar dependencias
echo ""
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Verificando instalacion..."
python -c "from src.database import DatabaseManager; print('OK Base de datos OK')"
python -c "import requests; print('OK requests OK')"
python -c "from bs4 import BeautifulSoup; print('OK BeautifulSoup OK')"

echo ""
echo "=========================================="
echo "FIX completado!"
echo "=========================================="
echo ""
echo "Ejecuta:"
echo "  source env/bin/activate"
echo "  python main.py"
echo ""

