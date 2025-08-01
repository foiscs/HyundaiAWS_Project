data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
# =========================================
# AWS Config -> S3 -> Splunk
# =========================================
# Configuration Recorder
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.project_name}-config-recorder"
  role_arn = aws_iam_role.config_role.arn
  recording_group {
    all_supported                 = var.record_all_resources
    include_global_resource_types = var.include_global_resources
    resource_types               = var.specific_resource_types
  }
  depends_on = [aws_config_delivery_channel.main]
}

# Delivery Channel
resource "aws_config_delivery_channel" "main" {
  name           = "${var.project_name}-config-delivery-channel"
  s3_bucket_name = var.s3_logs_bucket_name
  s3_key_prefix  = "aws-config"

  depends_on = [aws_s3_bucket_policy.config_bucket_policy]
}

# IAM Role for AWS Config
resource "aws_iam_role" "config_role" {
  name = "${var.project_name}-config-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-config-role"
    Component = "Security"
    Service   = "Config"
  })
}

# Attach AWS managed policy
resource "aws_iam_role_policy_attachment" "config_role_policy" {
  role       = aws_iam_role.config_role.name
  policy_arn = "arn:aws:iam::aws:policy/aws-service-role/AWSConfigServiceRolePolicy"
}

# =========================================
# Config Rules (Compliance Checks)
# =========================================
# EC2 Security Group Rules
resource "aws_config_config_rule" "ec2_security_group_attached" {
  count = var.enable_config_rules ? 1 : 0
  name  = "${var.project_name}-ec2-security-group-attached"
  source {
    owner             = "AWS"
    source_identifier = "EC2_SECURITY_GROUP_ATTACHED_TO_ENI"
  }
  depends_on = [aws_config_configuration_recorder.main]
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-ec2-sg-rule"
  })
}
# S3 Bucket Public Access
resource "aws_config_config_rule" "s3_bucket_public_access_prohibited" {
  count = var.enable_config_rules ? 1 : 0
  name  = "${var.project_name}-s3-bucket-public-access-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_ACCESS_PROHIBITED"
  }
  depends_on = [aws_config_configuration_recorder.main]
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-s3-public-access-rule"
  })
}
# EBS Encryption
resource "aws_config_config_rule" "ebs_encrypted_volumes" {
  count = var.enable_config_rules ? 1 : 0
  name  = "${var.project_name}-ebs-encrypted-volumes"
  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }
  depends_on = [aws_config_configuration_recorder.main]
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-ebs-encryption-rule"
  })
}
# RDS Encryption
resource "aws_config_config_rule" "rds_storage_encrypted" {
  count = var.enable_config_rules ? 1 : 0
  name  = "${var.project_name}-rds-storage-encrypted"
  source {
    owner             = "AWS"
    source_identifier = "RDS_STORAGE_ENCRYPTED"
  }
  depends_on = [aws_config_configuration_recorder.main]
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-rds-encryption-rule"
  })
}
# Root Access Key Check
resource "aws_config_config_rule" "root_access_key_check" {
  count = var.enable_config_rules ? 1 : 0
  name  = "${var.project_name}-root-access-key-check"
  source {
    owner             = "AWS"
    source_identifier = "ROOT_ACCESS_KEY_CHECK"
  }
  depends_on = [aws_config_configuration_recorder.main]
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-root-key-rule"
  })
}