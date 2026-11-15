#!/usr/bin/env bash
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
		try_files {path} {path}.html {path}/index.html /index.html
		file_server
	}
}
EOF

sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy

echo
echo "==> Done. memos removed; Caddy now serves only investlens.duckdns.org (backup at /etc/caddy/Caddyfile.bak)."
