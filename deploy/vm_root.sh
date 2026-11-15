#!/usr/bin/env bash
set -euo pipefail

SITE_USER="${SITE_USER:-$USER}"
APP_DIR="$HOME/trading"

echo "==> Security updates"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y full-upgrade
sudo apt-get install -y fail2ban unattended-upgrades
sudo systemctl enable --now fail2ban unattended-upgrades

echo "==> SSH: keys only, no root, only $USER"
sudo tee /etc/ssh/sshd_config.d/99-hardening.conf >/dev/null <<SSHD
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
MaxAuthTries 3
X11Forwarding no
AllowUsers $USER
SSHD
sudo sshd -t
sudo systemctl reload ssh

echo "==> Firewall: only SSH, HTTP, HTTPS"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable

echo "==> Unused services"
sudo systemctl disable --now docker.socket docker.service containerd.service 2>/dev/null || true
if dpkg -s slapd >/dev/null 2>&1; then
  read -r -p "Remove the OpenLDAP server (slapd), listening publicly on port 389? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] && sudo apt-get -y purge slapd && sudo apt-get -y autoremove
fi

echo "==> Site password (user: $SITE_USER)"
HASH="$(caddy hash-password)"
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
sudo tee /etc/caddy/Caddyfile >/dev/null <<CADDY
investlens.duckdns.org {
	encode zstd gzip

	@private not path /api/cb/*
	basic_auth @private {
		$SITE_USER $HASH
	}

	handle /api/* {
		reverse_proxy 127.0.0.1:8000
	}

	handle {
		root * $APP_DIR/frontend/dist
		try_files {path} {path}.html {path}/index.html /index.html
		file_server
	}
}
CADDY
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy

echo
echo "Done. Site login: $SITE_USER / the password you just typed."
[ -f /var/run/reboot-required ] && echo "A reboot is required for the kernel update: sudo reboot"
