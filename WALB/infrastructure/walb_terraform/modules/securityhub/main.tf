data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_securityhub_account" "main" {
    enable_default_standards = var.enable_default_standards
  }

  # Security Hub Standards Subscriptions
resource "aws_securityhub_standards_subscription" "aws_foundational" {
  count         = var.enable_aws_foundational ? 1 : 0
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/aws-foundational-security-best-practices/v/1.0.0"
  
  depends_on = [aws_securityhub_account.main]
}

resource "aws_securityhub_standards_subscription" "cis" {
  count         = var.enable_cis_standard ? 1 : 0
  standards_arn = "arn:aws:securityhub:${data.aws_region.current.name}::standards/cis-aws-foundations-benchmark/v/1.4.0"
  
  depends_on = [aws_securityhub_account.main]
}


# CloudWatch Log Group for Security Hub
resource "aws_cloudwatch_log_group" "security_hub_logs" {
  name              = "${var.project_name}-security-hub-logs"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-security-hub-logs"
    Component = "Security"
    Service   = "SecurityHub"
  })
}

# =========================================
# Kinesis Data Stream for Security Hub
# =========================================
resource "aws_kinesis_stream" "security_hub_stream" {
  name             = "security-hub-stream"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours
  encryption_type = "KMS"
  kms_key_id      = var.kms_key_arn
  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords",
  ]
  tags = merge(var.common_tags, {
    Name      = "security-hub-stream"
    Component = "Security"
    Service   = "Kinesis"
    Purpose   = "Security Hub Findings"
  })
}

# =========================================
# EventBridge Rule for Security Hub Findings
# =========================================
resource "aws_cloudwatch_event_rule" "security_hub_findings" {
  name        = "${var.project_name}-security-hub-findings"
  description = "Capture Security Hub findings"
  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        Severity = {
          Label = var.severity_levels
        }
        RecordState = ["ACTIVE"]
        WorkflowState = ["NEW", "NOTIFIED"]
      }
    }
  })
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-security-hub-findings"
    Component = "Security"
    Service   = "EventBridge"
  })
}

# EventBridge Target - CloudWatch Logs
resource "aws_cloudwatch_event_target" "security_hub_to_logs" {
  rule      = aws_cloudwatch_event_rule.security_hub_findings.name
  target_id = "SecurityHubToCloudWatchLogs"
  arn       = aws_cloudwatch_log_group.security_hub_logs.arn
  depends_on = [aws_cloudwatch_log_group.security_hub_logs]
}

# CloudWatch Logs Resource Policy for EventBridge
resource "aws_cloudwatch_log_resource_policy" "security_hub_logs_policy" {
  policy_name = "${var.project_name}-security-hub-logs-policy"
  
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EventBridgeLogsPolicy"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.security_hub_logs.arn}:*"
      }
    ]
  })
}

# CloudWatch Logs Subscription Filter
resource "aws_cloudwatch_log_subscription_filter" "security_hub_kinesis" {
  name            = "${var.project_name}-security-hub-to-kinesis"
  log_group_name  = aws_cloudwatch_log_group.security_hub_logs.name
  filter_pattern  = var.log_filter_pattern
  destination_arn = aws_kinesis_stream.security_hub_stream.arn
  role_arn        = var.cloudwatch_kinesis_role_arn
  depends_on = [
    aws_cloudwatch_log_group.security_hub_logs,
    aws_kinesis_stream.security_hub_stream,
    aws_cloudwatch_event_target.security_hub_to_logs
  ]
}