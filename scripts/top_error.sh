#!/usr/bin/env bash
# Cuenta los códigos de error CIE-#### en los tres logs (api, worker y database)
# y escribe el más frecuente en output/top_error.txt.
# Los avisos W-### no se cuentan: solo hay códigos CIE-.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p output

top=$(cat logs/*.log | grep -o 'CIE-[0-9]\+' | sort | uniq -c | sort -rn | head -n 1)

ocurrencias=$(echo "$top" | awk '{print $1}')
codigo=$(echo "$top" | awk '{print $2}')

{
    echo "codigo_error=$codigo"
    echo "ocurrencias=$ocurrencias"
} > output/top_error.txt

cat output/top_error.txt
