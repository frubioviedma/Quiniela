#!/usr/bin/env bash
set -euo pipefail
echo "== Quiniela Pro - Compilación APK (Buildozer) =="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
APP_DIR="$ROOT/app_android"

if ! command -v buildozer >/dev/null 2>&1; then
  echo "buildozer no encontrado. Instálalo con: pip install buildozer"
  exit 1
fi

export QUINIELA_DEV_MODE=1
cd "$APP_DIR"
buildozer android debug
echo
echo "APK generado (carpeta bin/). Puedes instalarlo con:"
echo "  adb install -r bin/*.apk"

