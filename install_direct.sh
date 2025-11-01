#!/bin/bash

# Instalación directa para Python 3.13 con --break-system-packages
# SOLO usar si no puedes instalar python3-venv

echo "=========================================="
echo "Instalación Directa (Sin venv)"
echo "=========================================="
echo ""
echo "ATENCIÓN: Esta opción instala paquetes directamente en el sistema"
echo "Se usa --break-system-packages para bypassear PEP 668"
echo ""
echo "¿Continuar? (s/n)"
read -r respuesta

if [ "$respuesta" != "s" ] && [ "$respuesta" != "S" ]; then
    echo "Instalación cancelada"
    exit 0
fi

echo ""
echo "Instalando dependencias..."
pip3 install --break-system-packages --user -r requirements.txt

echo ""
echo "Verificando instalación..."
python3 -c "from src.database import DatabaseManager; from src.config import DB_PATH; print('OK Instalacion correcta')"

echo ""
echo "=========================================="
echo "Instalación completada!"
echo "=========================================="
echo ""
echo "Ejecuta: python3 main.py"
echo ""

