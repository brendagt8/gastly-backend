resource "aws_db_instance" "gastly" {
  identifier     = "gastly-db"
  engine         = "postgres"
  engine_version = "17"
  instance_class = var.rds_instance_class

  db_name  = "gastly"
  username = "gastly"
  password = var.db_password

  # Storage mínimo de RDS (20GB gp3 ≈ $2.30/mes), cifrado sin costo extra
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  # ── Decisiones de costo ──
  multi_az                     = false # Multi-AZ duplica el costo; innecesario en dev
  performance_insights_enabled = false # cuesta extra
  monitoring_interval          = 0     # enhanced monitoring cuesta extra
  backup_retention_period      = 1     # 1 día de backups (gratis hasta el tamaño de la BD)

  # Accesible desde internet pero el security group solo permite
  # la EC2 y tu IP — es lo que te da acceso directo con TablePlus/psql
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.rds.id]

  # BD de desarrollo sin datos críticos: destruir sin snapshot final
  skip_final_snapshot = true
  deletion_protection = false

  auto_minor_version_upgrade = true
  apply_immediately          = true
}
