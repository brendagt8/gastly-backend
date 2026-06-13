#!/bin/bash
# Bootstrap de la EC2: corre una sola vez al crear la instancia.
# Instala Python + Caddy y deja los servicios listos; el código de la app
# se sube después con terraform/scripts/deploy.sh
set -euxo pipefail

dnf update -y
dnf install -y python3.12 git rsync

# Directorio de la app, propiedad de ec2-user (deploy.sh hace rsync como ec2-user)
mkdir -p /opt/gastly/app
chown -R ec2-user:ec2-user /opt/gastly

# ── Caddy: HTTPS automático con Let's Encrypt sobre ${api_domain} ──
curl -fsSL -o /usr/local/bin/caddy "https://caddyserver.com/api/download?os=linux&arch=arm64"
chmod +x /usr/local/bin/caddy

mkdir -p /etc/caddy
cat > /etc/caddy/Caddyfile <<EOF
${api_domain} {
    reverse_proxy 127.0.0.1:8000
}
EOF

cat > /etc/systemd/system/caddy.service <<'EOF'
[Unit]
Description=Caddy reverse proxy (HTTPS)
After=network-online.target

[Service]
ExecStart=/usr/local/bin/caddy run --config /etc/caddy/Caddyfile
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ── Backend FastAPI como servicio ──
cat > /etc/systemd/system/gastly.service <<'EOF'
[Unit]
Description=Gastly API (FastAPI + uvicorn)
After=network-online.target

[Service]
User=ec2-user
WorkingDirectory=/opt/gastly/app
EnvironmentFile=/opt/gastly/.env
ExecStart=/opt/gastly/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now caddy
# gastly se habilita pero arrancará cuando exista venv + .env (primer deploy)
systemctl enable gastly
