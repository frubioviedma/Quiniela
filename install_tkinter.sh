#!/bin/bash

# Script para instalar tkinter en Linux/WSL

echo "=========================================="
echo "Instalación de tkinter para Linux/WSL"
echo "=========================================="

# Detectar versión de Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)

echo "Detectada versión de Python: $PYTHON_VERSION"

# Instalar python3-tk según la versión
if command -v apt &> /dev/null; then
    echo "Ubuntu/Debian detectado"
    
    case $PYTHON_VERSION in
        3.13)
            echo "Instalando python3.13-tk..."
            sudo apt update
            sudo apt install -y python3.13-tk
            ;;
        3.12)
            echo "Instalando python3.12-tk..."
            sudo apt update
            sudo apt install -y python3.12-tk
            ;;
        3.11)
            echo "Instalando python3.11-tk..."
            sudo apt update
            sudo apt install -y python3.11-tk
            ;;
        3.10)
            echo "Instalando python3-tk..."
            sudo apt update
            sudo apt install -y python3-tk
            ;;
        *)
            echo "Intentando instalar python3-tk genérico..."
            sudo apt update
            sudo apt install -y python3-tk
            ;;
    esac
    
    echo ""
    echo "Verificando instalación..."
    python3 -c "import tkinter; print('✓ tkinter instalado correctamente')"
    
elif command -v yum &> /dev/null; then
    echo "RHEL/CentOS detectado"
    sudo yum install -y python3-tkinter
elif command -v dnf &> /dev/null; then
    echo "Fedora detectado"
    sudo dnf install -y python3-tkinter
else
    echo "Gestor de paquetes no detectado. Instala manualmente según tu distribución."
    exit 1
fi

echo ""
echo "=========================================="
echo "Instalación completada!"
echo "=========================================="
echo ""
echo "Ejecuta: python3 main.py"
echo ""

