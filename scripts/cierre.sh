#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Cierre mensual de afiliados activos (script heredado de Operaciones).
# Autor original: equipo de sistemas 2019. Última modificación: "temporal".
# ---------------------------------------------------------------------------
set -e

ENTRADA=data
SALIDA=output
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$SALIDA"

if python3 -c "import csv" >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/cierre.py"
else
  python "$SCRIPT_DIR/cierre.py"
fi
