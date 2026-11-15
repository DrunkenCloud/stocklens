#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-135.235.195.168}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Building frontend"
npm --prefix frontend run build >/dev/null

echo "==> Syncing code"
rsync -az --delete \
  --exclude '.git/' --exclude '.env' --exclude '.venv/' --exclude 'node_modules/' \
  --exclude 'frontend/.next/' --exclude 'frontend/out/' --exclude 'frontend/dist/' \
  --exclude 'pipeline/logs/' --exclude 'logs/' --exclude '*.log' --exclude '__pycache__/' \
  --exclude '.superpowers/' --exclude '.playwright-mcp/' \
  ./ "$HOST:trading/"
rsync -az --delete frontend/out/ "$HOST:trading/frontend/dist/"

echo "==> Migrating, installing units, restarting"
ssh "$HOST" 'bash -s' <<'REMOTE'
set -euo pipefail
cd ~/trading
pipeline/.venv/bin/pip install -q -r pipeline/requirements.txt
backend/.venv/bin/pip install -q -r backend/requirements.txt
pipeline/.venv/bin/python db/migrate.py --seed
mkdir -p ~/.config/systemd/user
for unit in ~/trading/deploy/systemd/*; do ln -sf "$unit" ~/.config/systemd/user/"$(basename "$unit")"; done
systemctl --user daemon-reload
systemctl --user enable --now stocklens-prices.timer stocklens-fundamentals.timer stocklens-securities.timer
systemctl --user enable stocklens-backend.service
systemctl --user restart stocklens-backend.service
crontab -l 2>/dev/null | grep -v "trading/pipeline/run_job.sh" | crontab - || true
sleep 2
curl -fsS http://127.0.0.1:8000/api/health
REMOTE
echo
echo "Deployed."
