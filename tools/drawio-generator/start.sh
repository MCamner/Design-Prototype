#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo "⚠️  Ingen .env-fil hittades."
  echo "   Kopiera .env.example till .env och fyll i din OPENAI_API_KEY:"
  echo ""
  echo "   cp .env.example .env"
  echo "   # Redigera .env och lägg in din API-nyckel"
  echo ""
  exit 1
fi

set -a
. ./.env
set +a

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x /opt/homebrew/opt/python@3.11/libexec/bin/python3 ]; then
    PYTHON_BIN=/opt/homebrew/opt/python@3.11/libexec/bin/python3
  else
    PYTHON_BIN=python3
  fi
fi

echo "◈ Startar draw.io Diagramgenerator..."
echo "  → OpenAI-modell: ${OPENAI_MODEL:-gpt-5-mini}"
echo "  → Python: $("$PYTHON_BIN" --version 2>&1)"
echo "  → http://localhost:${PORT:-5000}"
echo "  (Ctrl+C för att stoppa)"
echo ""

"$PYTHON_BIN" server.py
