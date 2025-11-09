#!/bin/bash
# Script para crear un punto de control (checkpoint) antes de cambios importantes
# Uso: ./crear_checkpoint.sh "descripcion-del-cambio"

if [ -z "$1" ]; then
    echo "Error: Debes proporcionar una descripción del cambio"
    echo "Uso: ./crear_checkpoint.sh 'descripcion-del-cambio'"
    exit 1
fi

DESCRIPCION="$1"
# Crear nombre de rama: checkpoint-descripcion (sin espacios, en minúsculas)
NOMBRE_RAMA=$(echo "checkpoint-$DESCRIPCION" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g')
FECHA=$(date +"%Y-%m-%d %H:%M:%S")

echo "=========================================="
echo "Creando punto de control..."
echo "=========================================="
echo "Rama: $NOMBRE_RAMA"
echo "Descripción: $DESCRIPCION"
echo "Fecha: $FECHA"
echo ""

# Verificar que estamos en main o en una rama limpia
BRANCH_ACTUAL=$(git branch --show-current)
echo "Rama actual: $BRANCH_ACTUAL"

# Verificar si hay cambios sin commitear
if ! git diff-index --quiet HEAD --; then
    echo ""
    echo "Hay cambios sin commitear. ¿Deseas continuar? (s/n)"
    read -r respuesta
    if [ "$respuesta" != "s" ] && [ "$respuesta" != "S" ]; then
        echo "Operación cancelada."
        exit 1
    fi
fi

# Crear nueva rama desde la actual
echo ""
echo "Creando rama: $NOMBRE_RAMA"
git checkout -b "$NOMBRE_RAMA"

# Añadir todos los cambios
echo "Añadiendo cambios..."
git add -A

# Hacer commit con mensaje descriptivo
MENSAJE_COMMIT="CHECKPOINT: $DESCRIPCION - $FECHA"
echo "Haciendo commit..."
git commit -m "$MENSAJE_COMMIT"

# Push a remoto
echo "Subiendo a GitHub..."
git push -u origin "$NOMBRE_RAMA"

echo ""
echo "=========================================="
echo "✓ Punto de control creado exitosamente"
echo "=========================================="
echo "Rama: $NOMBRE_RAMA"
echo "Commit: $(git rev-parse --short HEAD)"
echo ""
echo "Para volver a main: git checkout main"
echo "Para restaurar este checkpoint: git checkout $NOMBRE_RAMA"
echo ""

