variable "aws_region" {
  description = "Región AWS (us-east-1 es la más barata)"
  type        = string
  default     = "us-east-1"
}

variable "my_ip_cidr" {
  description = "Tu IP pública en formato CIDR (ej. 189.123.45.67/32) para SSH y acceso directo a la BD. Obtenla con: curl -s ifconfig.me"
  type        = string
}

variable "ssh_public_key" {
  description = "Llave pública SSH para la EC2. Generar con: ssh-keygen -t ed25519 -f ~/.ssh/gastly"
  type        = string
}

variable "db_password" {
  description = "Password del usuario gastly en RDS (mínimo 8 caracteres)"
  type        = string
  sensitive   = true
}

variable "notification_email" {
  description = "Email para alertas de presupuesto"
  type        = string
  default     = "brendalopezgft@gmail.com"
}

variable "ec2_instance_type" {
  description = "Tipo de instancia EC2 (ARM es ~20% más barato que x86)"
  type        = string
  default     = "t4g.micro" # 2 vCPU, 1GB RAM ≈ $6/mes 24/7
}

variable "rds_instance_class" {
  description = "Clase de instancia RDS"
  type        = string
  default     = "db.t4g.micro" # 2 vCPU, 1GB RAM ≈ $12/mes 24/7
}

variable "monthly_budget_usd" {
  description = "Presupuesto mensual en USD para las alertas"
  type        = string
  default     = "30"
}
