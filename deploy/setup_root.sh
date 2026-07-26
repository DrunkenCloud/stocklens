#!/usr/bin/env bash
# One-time root setup for deploying StockLens on the VPS. Run this YOURSELF
# (sudo will prompt for your own password locally - it's never sent to or
# seen by Claude, which cannot run privileged commands over a non-interactive
# SSH session). See 06_DECISIONS.md D10 for why this is the entire root
# footprint: one apt install, one DB role/database, one linger enable.
# Everything else in the deploy runs as your regular user, no sudo needed.
#
# Usage: scp this to the VM (or it'll already be there via the rsync step),
# then: bash deploy/setup_root.sh
set -euo pipefail

echo "==> Installing PostgreSQL and python3-venv"
sudo apt update
sudo apt install -y postgresql python3.10-venv

echo "==> Creating stocklens DB role + database (safe to re-run)"
ROLE_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='stocklens'")
if [ "$ROLE_EXISTS" != "1" ]; then
    DB_PASS=$(openssl rand -hex 16)
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE USER stocklens WITH PASSWORD '$DB_PASS';"
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE stocklens OWNER stocklens;"
    echo
    echo "==> Save this into ~/trading/.env as DATABASE_URL:"
    echo "DATABASE_URL=postgresql://stocklens:${DB_PASS}@localhost:5432/stocklens"
else
    echo "stocklens role already exists - password unchanged, not reprinting it."
    echo "(if you lost it: sudo -u postgres psql -c \"ALTER USER stocklens WITH PASSWORD 'newpass';\")"
fi

echo "==> Enabling linger for $USER (lets systemctl --user services survive logout/reboot)"
sudo loginctl enable-linger "$USER"

echo
echo "==> Done. Root setup complete - nothing else in this deploy needs sudo."
