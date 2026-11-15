#!/usr/bin/env bash
# Removes the old "memos" diary app from the VPS and makes the StockLens Caddy
# site persistent. Run it YOURSELF on the VM (needs sudo, which prompts for
# your password):  ssh -t 135.235.195.168 'bash ~/trading/deploy/remove_memos.sh'
#
# Why the Caddyfile rewrite: the investlens.duckdns.org route was originally
# added only to Caddy's in-memory config via its admin API, so it vanished on
# the Nov 6 reboot (Caddy reloads /etc/caddy/Caddyfile on start). Writing it
# into the Caddyfile makes it survive restarts.
set -euo pipefail

echo "This permanently deletes memos, including your diary data in ~/.memos/memos_prod.db."
read -r -p "Type 'delete' to continue: " answer
[ "$answer" = "delete" ] || { echo "Aborted."; exit 1; }

echo "==> Stopping and disabling memos.service"
sudo systemctl disable --now memos.service || true
sudo rm -f /etc/systemd/system/memos.service
sudo systemctl daemon-reload
sudo systemctl reset-failed memos.service 2>/dev/null || true

echo "==> Removing memos binary, config and data"
sudo rm -f /usr/local/bin/memos
sudo rm -rf /etc/memos
# memos_app/memos_dev.db is root-owned, hence sudo
sudo rm -rf "$HOME/memos_app" "$HOME/.memos" "$HOME"/memos_backup_*.db

echo "==> Writing /etc/caddy/Caddyfile (StockLens only)"
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
investlens.duckdns.org {
	encode zstd gzip

	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle {
		root * $HOME/trading/frontend/dist
		# frontend builds with trailingSlash: true, so pages are <route>/index.html;
		# /index.html is the fallback for unknown paths.
		try_files {path} {path}.html {path}/index.html /index.html
		file_server
	}
}
EOF

sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy

echo
echo "==> Done. memos removed; Caddy now serves only investlens.duckdns.org (backup at /etc/caddy/Caddyfile.bak)."
