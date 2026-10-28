#!/usr/bin/env bash
# OpenValora - Script de Inicialização Rápida

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  Iniciando OpenValora - Engenharia de Avaliações"
echo "=========================================================="

if command -v uv >/dev/null 2>&1; then
    exec uv run python3 main.py "$@"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    exec python3 main.py "$@"
else
    exec python3 main.py "$@"
fi
