#!/usr/bin/env bash
# Enciende RDS y EC2. La RDS tarda ~5-10 min en estar disponible;
# el backend reintenta solo (systemd Restart=on-failure), así que no
# importa que la EC2 arranque antes que la BD.
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="us-east-1"
INSTANCE_ID=$(terraform output -raw ec2_instance_id)

echo "Encendiendo RDS gastly-db (tarda unos minutos)..."
aws rds start-db-instance --region "$REGION" --db-instance-identifier gastly-db > /dev/null

echo "Encendiendo EC2 $INSTANCE_ID..."
aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID" > /dev/null

echo "Listo. La API estará en $(terraform output -raw api_url) en unos minutos."
