#!/usr/bin/env bash
set -euo pipefail
echo "== Quiniela Pro - Lanzador de desarrollo =="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
export QUINIELA_DEV_MODE=1
python3 "$ROOT/scripts/run_app.py" "$@"

