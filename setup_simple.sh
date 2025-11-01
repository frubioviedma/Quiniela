#!/bin/bash

# Setup simple para Ubuntu/Python 3.13 sin venv

echo "=========================================="
echo "Setup Sistema de Quiniela (Simple)"
echo "=========================================="

# Verificar si python3-venv está instalado
if python3 -m venv --help &> /dev/null; then
    echo "Python venv disponible - creando entorno virtual..."
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    echo ""
    echo "✓ Instalación completa!"
    echo "Para usar: source env/bin/activate && python main.py"
else
    echo "Python venv NO disponible"
    echo ""
    echo "OPCION 1: Instalar python3-venv (Recomendado)"
    echo "  sudo apt install python3-venv"
    echo ""
    echo "OPCION 2: Usar --break-system-packages (NO recomendado)"
    echo "  pip3 install --break-system-packages --user -r requirements.txt"
    echo ""
    echo "OPCION 3: Instalar python3-full"
    echo "  sudo apt install python3-full"
    echo "  python3 -m venv env"
    exit 1
fi

