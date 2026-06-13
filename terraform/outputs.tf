output "api_url" {
  description = "URL pública del backend (ponla en EXPO_PUBLIC_API_URL al compilar la app)"
  value       = "https://${local.api_domain}"
}

output "ec2_public_ip" {
  description = "IP fija de la EC2"
  value       = aws_eip.gastly.public_ip
}

output "ec2_instance_id" {
  description = "ID de la instancia (para los scripts de stop/start)"
  value       = aws_instance.gastly.id
}

output "ssh_command" {
  description = "Conectarse a la EC2"
  value       = "ssh -i ~/.ssh/gastly ec2-user@${aws_eip.gastly.public_ip}"
}

output "rds_endpoint" {
  description = "Endpoint de PostgreSQL (úsalo en TablePlus y en DATABASE_URL)"
  value       = aws_db_instance.gastly.endpoint
}

output "database_url" {
  description = "DATABASE_URL para el .env de producción"
  value       = "postgresql+asyncpg://gastly:${var.db_password}@${aws_db_instance.gastly.endpoint}/gastly?ssl=require"
  sensitive   = true
}
