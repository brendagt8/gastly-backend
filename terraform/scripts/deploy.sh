#!/usr/bin/env bash
# Sube el backend a la EC2 y reinicia el servicio.
# Uso: ./scripts/deploy.sh   (lee la IP del output de terraform)
# Requiere: gastly-backend/.env.production con la config de prod
set -euo pipefail
cd "$(dirname "$0")/.."

KEY="${SSH_KEY:-$HOME/.ssh/gastly}"
IP=$(terraform output -raw ec2_public_ip)
HOST="ec2-user@$IP"
BACKEND_DIR="$(cd .. && pwd)"

if [ ! -f "$BACKEND_DIR/.env.production" ]; then
  echo "Falta $BACKEND_DIR/.env.production — créalo desde .env.production.example" >&2
  exit 1
fi

echo "Subiendo código a $IP..."
rsync -az --delete -e "ssh -i $KEY" \
  --exclude '.venv' --exclude '.git' --exclude '__pycache__' \
  --exclude '.env*' --exclude 'terraform' \
  "$BACKEND_DIR/" "$HOST:/opt/gastly/app/"

scp -q -i "$KEY" "$BACKEND_DIR/.env.production" "$HOST:/opt/gastly/.env"

echo "Instalando dependencias y reiniciando..."
ssh -i "$KEY" "$HOST" '
  set -e
  cd /opt/gastly
  [ -d venv ] || python3.12 -m venv venv
  venv/bin/pip install -q --upgrade pip
  venv/bin/pip install -q -r app/requirements.txt
  sudo systemctl restart gastly
  sleep 3
  curl -fsS http://127.0.0.1:8000/health
'
echo ""
echo "✓ Backend desplegado en $(terraform output -raw api_url)"
