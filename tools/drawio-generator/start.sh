#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo "⚠️  Ingen .env-fil hittades."
  echo "   Kopiera .env.example till .env och fyll i din ANTHROPIC_API_KEY:"
  echo ""
  echo "   cp .env.example .env"
  echo "   # Redigera .env och lägg in din API-nyckel"
  echo ""
  exit 1
fi

echo "◈ Startar draw.io Diagramgenerator..."
echo "  → http://localhost:${PORT:-5000}"
echo "  (Ctrl+C för att stoppa)"
echo ""

python3 server.py
