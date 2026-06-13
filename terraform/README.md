# Infraestructura de Gastly en AWS

EC2 t4g.micro (backend, systemd + Caddy con HTTPS) + RDS PostgreSQL db.t4g.micro,
en us-east-1 sobre la VPC default. Sin NAT, sin ALB, sin Multi-AZ — optimizado
para una cuenta nueva con créditos.

```
iPhone ── https://<ip>.sslip.io ──> EC2 (Caddy → uvicorn :8000) ──> RDS Postgres
                                     │ SG: 80/443 público, 22 mi IP   │ SG: EC2 + mi IP
```

## Primer despliegue

```bash
# 1. Llave SSH y variables
ssh-keygen -t ed25519 -f ~/.ssh/gastly
cp terraform.tfvars.example terraform.tfvars   # llena IP, llave y password de BD

# 2. Crear infraestructura (~10 min, RDS es lento)
terraform init
terraform apply

# 3. Config de producción
cd .. && cp .env.production.example .env.production
terraform -chdir=terraform output database_url   # → DATABASE_URL
terraform -chdir=terraform output api_url        # → APP_URL y GOOGLE_REDIRECT_URI
# Genera SECRET_KEY y TOKEN_ENCRYPTION_KEY nuevos (instrucciones en el archivo)

# 4. Google Cloud Console → Credentials → OAuth client:
#    agrega https://<api_url>/auth/google/callback a las redirect URIs

# 5. Desplegar backend (crea tablas y seed solo en el primer arranque)
cd terraform && ./scripts/deploy.sh

# 6. Compilar la app apuntando a producción
cd ../../gastly-app
EXPO_PUBLIC_API_URL=$(terraform -chdir=../gastly-backend/terraform output -raw api_url) \
  npx expo run:ios --device 00008150-001928360E86401C --configuration Release
```

## Operación diaria

| Acción | Comando |
|---|---|
| Apagar todo (ahorrar créditos) | `./scripts/stop.sh` |
| Encender todo | `./scripts/start.sh` (RDS tarda ~5-10 min) |
| Re-desplegar cambios del backend | `./scripts/deploy.sh` |
| Ver logs del backend | `ssh -i ~/.ssh/gastly ec2-user@<ip> journalctl -u gastly -f` |
| Conectar TablePlus/psql a la BD | host del output `rds_endpoint`, user `gastly`, BD `gastly`, SSL requerido |
| Destruir todo | `terraform destroy` (la BD se pierde — sin datos críticos no pasa nada) |

## Costos aproximados (us-east-1, 24/7)

| Recurso | $/mes |
|---|---|
| EC2 t4g.micro | ~$6.10 |
| RDS db.t4g.micro | ~$11.70 |
| Storage RDS 20GB gp3 | ~$2.30 |
| EBS 10GB gp3 | ~$0.80 |
| Elastic IP | ~$3.65 (se cobra incluso apagada la EC2) |
| **Total prendido 24/7** | **~$25** |
| **Total apagando cuando no pruebas** | **~$10–15** |

Alertas de presupuesto por email al 50/80/100% de $30/mes (configuradas por terraform).

## Notas

- **RDS apagada NO pierde datos** — solo se cobra el storage. Pero AWS la
  **reinicia sola a los 7 días**; si pausas más tiempo, re-corre `stop.sh` o
  haz snapshot + `terraform destroy`.
- La IP cambia solo si haces `terraform destroy`; stop/start la conservan
  (por eso la EIP). Si la destruyes, hay que actualizar la redirect URI en
  Google y recompilar la app.
- HTTPS sale de sslip.io + Let's Encrypt vía Caddy, sin comprar dominio. Si
  Let's Encrypt llega a fallar por rate-limit del dominio compartido sslip.io,
  Caddy cae automáticamente a ZeroSSL.
- El esquema de la BD se crea solo en el primer arranque del backend
  (create_all + seed de categorías y remitentes bancarios).
