#!/bin/bash

# Setup completo del Sistema de Quiniela para Linux/WSL

echo "=========================================="
echo "Setup Completo - Sistema de Quiniela"
echo "=========================================="
echo ""

# Instalar tkinter primero
echo "1. Instalando tkinter..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
echo "Versión de Python detectada: $PYTHON_VERSION"

if command -v apt &> /dev/null; then
    if [[ $PYTHON_VERSION == "3.13" ]]; then
        sudo apt update && sudo apt install -y python3.13-tk python3-venv || true
    elif [[ $PYTHON_VERSION == "3.12" ]]; then
        sudo apt update && sudo apt install -y python3.12-tk python3-venv || true
    else
        sudo apt update && sudo apt install -y python3-tk python3-venv || true
    fi
fi

# Crear venv si no existe
if [ ! -d "env" ]; then
    echo ""
    echo "2. Creando entorno virtual..."
    python3 -m venv env || {
        echo "ERROR: No se pudo crear venv. Instala python3-venv:"
        echo "  sudo apt install python3-venv"
        exit 1
    }
fi

# Activar venv
echo ""
echo "3. Activando entorno virtual..."
source env/bin/activate

# Instalar dependencias
echo ""
echo "4. Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar
echo ""
echo "5. Verificando instalación..."
python -c "from src.database import DatabaseManager; from tkinter import Tk; print('OK Instalacion correcta!')" || {
    echo "ERROR en verificacion"
    exit 1
}

echo ""
echo "=========================================="
echo "Setup completado exitosamente!"
echo "=========================================="
echo ""
echo "Para ejecutar la aplicacion:"
echo "  source env/bin/activate"
echo "  python main.py"
echo ""

