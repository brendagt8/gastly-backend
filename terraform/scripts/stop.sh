#!/usr/bin/env bash
# Apaga EC2 y RDS para no gastar créditos cuando no estés probando.
# Mientras están apagadas solo pagas storage (~$3/mes) + la EIP (~$3.6/mes).
# OJO: AWS reinicia la RDS automáticamente a los 7 días de apagada —
# si vas a pausar más tiempo, vuelve a correr este script o haz snapshot+destroy.
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="us-east-1"
INSTANCE_ID=$(terraform output -raw ec2_instance_id)

echo "Apagando EC2 $INSTANCE_ID..."
aws ec2 stop-instances --region "$REGION" --instance-ids "$INSTANCE_ID" > /dev/null

echo "Apagando RDS gastly-db..."
aws rds stop-db-instance --region "$REGION" --db-instance-identifier gastly-db > /dev/null

echo "Listo. Para encender de nuevo: ./scripts/start.sh"
