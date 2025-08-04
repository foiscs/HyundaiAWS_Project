data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
# =========================================
# VPC Flow Logs to S3 Only
# =========================================
resource "aws_flow_log" "vpc_flow_logs" {
  log_destination      = var.vpc_flow_logs_s3_arn
  log_destination_type = "s3"
  traffic_type         = var.traffic_type
  vpc_id              = var.vpc_id  # ✅ 변수로 전달받음
  # S3 파티셔닝 옵션
  destination_options {
    file_format                = "plain-text"
    hive_compatible_partitions = var.enable_hive_partitions
    per_hour_partition        = var.enable_hourly_partitions
  }
  log_format = var.vpc_flow_logs_format
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-vpc-flow-logs"
    Component = "Security"
    Service   = "VPCFlowLogs"
    Purpose   = "Network Traffic Analysis"
  })
}
# =========================================
# S3 Lifecycle Configuration (Optional)
# =========================================
resource "aws_s3_bucket_lifecycle_configuration" "vpc_flow_logs_lifecycle" {
  count  = var.enable_s3_lifecycle ? 1 : 0
  bucket = var.s3_bucket_name
  rule {
    id     = "vpc-flow-logs-lifecycle"
    status = "Enabled"
    filter {
      prefix = "vpc-flow-logs/"
    }
    transition {
      days          = var.transition_to_ia_days
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = var.transition_to_glacier_days
      storage_class = "GLACIER"
    }
    transition {
      days          = var.transition_to_deep_archive_days
      storage_class = "DEEP_ARCHIVE"
    }
    expiration {
      days = var.vpc_flow_logs_retention_days
    }
  }
}