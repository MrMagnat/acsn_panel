#!/bin/bash
set -e

echo "=== ASCN AI Platform ==="
echo ""

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# ── Backend ────────────────────────────────────────────────────────────────
echo "▶ Запускаю бэкенд..."
cd "$BACKEND"

if [ ! -d ".venv" ]; then
  echo "  Создаю venv и устанавливаю зависимости..."
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi

.venv/bin/alembic upgrade head

.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ── Frontend ───────────────────────────────────────────────────────────────
echo "▶ Запускаю фронтенд..."
cd "$FRONTEND"

if [ ! -d "node_modules" ]; then
  echo "  Устанавливаю npm пакеты..."
  npm install
fi

[ ! -f ".env" ] && echo "VITE_API_URL=http://localhost:8000" > .env

npm run dev -- --host &
FRONTEND_PID=$!

# ── Готово ─────────────────────────────────────────────────────────────────
sleep 3
echo ""
echo "✅ Платформа запущена!"
echo ""
echo "   Frontend:  http://localhost:5173"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "   Admin:     admin@ascn.io  /  admin123"
echo ""
echo "   Ctrl+C — остановить"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
