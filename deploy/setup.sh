#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNITS="$HOME/.config/systemd/user"

echo "==> System packages, ports, hosts entry, boot settings (sudo)"
if ! command -v caddy >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y caddy libnss3-tools
fi
sudo systemctl disable --now caddy.service 2>/dev/null || true
sudo setcap cap_net_bind_service=+ep "$(readlink -f /usr/bin/caddy)"
grep -q "investlens.duckdns.org" /etc/hosts || printf '127.0.0.1 investlens.duckdns.org\n::1 investlens.duckdns.org\n' | sudo tee -a /etc/hosts >/dev/null
sudo systemctl enable --now docker.service
sudo loginctl enable-linger "$USER"

echo "==> Database"
cd "$ROOT"
docker compose up -d db
until docker compose exec -T db pg_isready -U stocklens >/dev/null 2>&1; do sleep 1; done
pipeline/.venv/bin/python db/migrate.py --seed

echo "==> Frontend build"
npm --prefix frontend run build >/dev/null

echo "==> User services and timers"
mkdir -p "$UNITS"
for unit in "$ROOT"/deploy/systemd/*; do ln -sf "$unit" "$UNITS/$(basename "$unit")"; done
systemctl --user daemon-reload
systemctl --user enable --now stocklens-backend.service stocklens-caddy.service
systemctl --user enable --now stocklens-prices.timer stocklens-fundamentals.timer stocklens-securities.timer

echo "==> Trusting Caddy's local certificate (sudo)"
until curl -s -o /dev/null http://localhost:2019/config/; do sleep 1; done
caddy trust

echo
echo "Done. Open https://investlens.duckdns.org (restart the browser if it still warns about the certificate)."
