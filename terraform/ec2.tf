# AMI de Amazon Linux 2023 para ARM, siempre la más reciente
data "aws_ssm_parameter" "al2023_arm" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_key_pair" "gastly" {
  key_name   = "gastly"
  public_key = var.ssh_public_key
}

# IP fija: el dominio HTTPS y la config de la app dependen de ella, así que
# debe sobrevivir a los stop/start de la instancia.
# Ojo: las IPv4 públicas cuestan ~$3.6/mes y la EIP se cobra incluso con la
# instancia apagada — es el precio de no tener que reconfigurar la app.
resource "aws_eip" "gastly" {
  domain = "vpc"
}

locals {
  # sslip.io resuelve <ip-con-guiones>.sslip.io → la IP, lo que permite a
  # Caddy emitir un certificado HTTPS real sin comprar dominio.
  api_domain = "${replace(aws_eip.gastly.public_ip, ".", "-")}.sslip.io"
}

resource "aws_instance" "gastly" {
  ami                    = data.aws_ssm_parameter.al2023_arm.value
  instance_type          = var.ec2_instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = aws_key_pair.gastly.key_name

  user_data = templatefile("${path.module}/user_data.sh", {
    api_domain = local.api_domain
  })

  root_block_device {
    volume_type = "gp3"
    volume_size = 10 # GB ≈ $0.80/mes
  }

  metadata_options {
    http_tokens = "required" # IMDSv2 obligatorio
  }

  tags = {
    Name = "gastly-backend"
  }
}

resource "aws_eip_association" "gastly" {
  instance_id   = aws_instance.gastly.id
  allocation_id = aws_eip.gastly.id
}
