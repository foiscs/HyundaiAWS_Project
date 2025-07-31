# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Create CloudWatch Log Group for CloudTrail
resource "aws_cloudwatch_log_group" "cloudtrail_logs" {
  name              = "${var.project_name}-cloudtrail-logs"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-cloudtrail-logs"
    Component = "Security"
    Service   = "CloudTrail"
  })
}

# Kinesis Data Stream for CloudTrail Logs
resource "aws_kinesis_stream" "cloudtrail_stream" {
  name             = "cloudtrail-stream"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours

  encryption_type = "KMS"
  kms_key_id      = var.kms_key_arn

  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords",
  ]

  tags = merge(var.common_tags, {
    Name      = "cloudtrail-stream"
    Component = "Security"
    Service   = "Kinesis"
    Purpose   = "CloudTrail Log Streaming"
  })
}

# =========================================
# CloudTrail
# =========================================
resource "aws_cloudtrail" "main" {
  name           = "${var.project_name}-cloudtrail"
  s3_bucket_name = var.s3_bucket_name

  # CloudWatch Logs 
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail_logs.arn}:*"
  cloud_watch_logs_role_arn  = var.cloudtrail_cloudwatch_role_arn

  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  dynamic "event_selector" {
    for_each = var.enable_data_events ? [1] : []
    content {
      read_write_type                 = "All"
      include_management_events       = true
      exclude_management_event_sources = []

      data_resource {
        type   = "AWS::S3::Object"
        values = ["${var.s3_bucket_name}/*"]
      }
    }
  }

  dynamic "insight_selector" {
    for_each = var.enable_insights ? [1] : []
    content {
      insight_type = "ApiCallRateInsight"
    }
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-cloudtrail"
    Component = "Security"
    Service   = "CloudTrail"
  })

  depends_on = [aws_cloudwatch_log_group.cloudtrail_logs]
}

# =========================================
# CloudWatch Logs Subscription Filter
# =========================================
resource "aws_cloudwatch_log_subscription_filter" "cloudtrail_kinesis" {
  name            = "${var.project_name}-cloudtrail-to-kinesis"
  log_group_name  = aws_cloudwatch_log_group.cloudtrail_logs.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_stream.cloudtrail_stream.arn
  role_arn        = var.cloudwatch_kinesis_role_arn

  depends_on = [
    aws_cloudwatch_log_group.cloudtrail_logs,
    aws_kinesis_stream.cloudtrail_stream
  ]
}

