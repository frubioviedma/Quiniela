#!/bin/bash

# Script de instalación para Sistema de Quiniela
# Compatible con Linux/WSL/MacOS

echo "=========================================="
echo "Instalación Sistema de Quiniela"
echo "=========================================="
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Sistema: Linux"
    
    # Verificar si está en WSL
    if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null ; then
        echo "WSL detectado"
    fi
    
    # Verificar e instalar python3-venv si es necesario
    if ! python3 -m venv --help &> /dev/null; then
        echo ""
        echo "ATENCION: python3-venv no está instalado"
        echo "Por favor ejecuta:"
        echo "  sudo apt update"
        echo "  sudo apt install python3-venv"
        echo ""
        echo "O instala manualmente sin venv:"
        echo "  pip3 install --user -r requirements.txt"
        exit 1
    fi
    
    # Crear entorno virtual
    echo "Creando entorno virtual..."
    python3 -m venv env
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Sistema: macOS"
    echo "Creando entorno virtual..."
    python3 -m venv env
    
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Sistema: Windows"
    echo "Usando Python del sistema (no se crea venv en Windows)"
    ENV_PREFIX=""
else
    echo "Sistema no reconocido: $OSTYPE"
    echo "Intentando crear entorno virtual..."
    python3 -m venv env
fi

# Activar entorno virtual si existe
if [ -d "env" ]; then
    echo "Activando entorno virtual..."
    source env/bin/activate
    ENV_PREFIX=""
else
    echo "Usando Python del sistema"
    ENV_PREFIX="python3 -m"
fi

# Instalar tkinter si es Linux/WSL
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    echo "Instalando python3-tk para versión $PYTHON_VERSION..."
    if [[ $PYTHON_VERSION == "3.13" ]]; then
        sudo apt update && sudo apt install -y python3.13-tk 2>/dev/null || echo "tkinter ya instalado o no disponible"
    elif [[ $PYTHON_VERSION == "3.12" ]]; then
        sudo apt update && sudo apt install -y python3.12-tk 2>/dev/null || echo "tkinter ya instalado o no disponible"
    else
        sudo apt update && sudo apt install -y python3-tk 2>/dev/null || echo "tkinter ya instalado o no disponible"
    fi
fi

# Instalar dependencias
echo ""
echo "Instalando dependencias..."
pip install -r requirements.txt

# Verificar instalación
echo ""
echo "Verificando instalación..."
python -c "from src.database import DatabaseManager; from src.config import DB_PATH; print('✓ Módulos importados correctamente')"

echo ""
echo "=========================================="
echo "Instalación completada!"
echo "=========================================="
echo ""
echo "Para ejecutar la aplicación:"
echo "  source env/bin/activate    # Si usaste venv"
echo "  python main.py"
echo ""

