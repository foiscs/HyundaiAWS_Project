data "aws_caller_identity" "current"{}
data "aws_region" "current"{}

resource "aws_guardduty_detector" "main" {
  enable                       = true
  finding_publishing_frequency = var.finding_publishing_frequency
  # 직접 CloudWatch Logs 설정
  datasources {
    s3_logs {
      enable = var.enable_s3_protection
    }
    kubernetes {
      audit_logs {
        enable = var.enable_kubernetes_protection
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = var.enable_malware_protection
        }
      }
    }
  }
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-guardduty"
    Component = "Security"
    Service   = "GuardDuty"
  })
}


# CloudWatch Log Group for GuardDuty
resource "aws_cloudwatch_log_group" "guardduty_logs" {
  name              = "${var.project_name}-guardduty-logs"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-guardduty-logs"
    Component = "Security"
    Service   = "GuardDuty"
  })
}

resource "aws_guardduty_publishing_destination" "s3_logs" {
  detector_id     = aws_guardduty_detector.main.id
  destination_arn = var.s3_logs_bucket_arn
  kms_key_arn     = var.kms_key_arn
  
  destination_type = "S3"
}

# Kinesis Data Stream for GuardDuty
resource "aws_kinesis_stream" "guardduty_stream" {
  name             = "guardduty-stream"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours
  encryption_type = "KMS"
  kms_key_id      = var.kms_key_arn
  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords",
  ]
  tags = merge(var.common_tags, {
    Name      = "guardduty-stream"
    Component = "Security"
    Service   = "Kinesis"
    Purpose   = "GuardDuty Findings"
  })
}

  resource "aws_cloudwatch_log_subscription_filter" "guardduty_kinesis" {
    name            = "${var.project_name}-guardduty-to-kinesis"
    log_group_name  = aws_cloudwatch_log_group.guardduty_logs.name
    filter_pattern  = var.log_filter_pattern
    destination_arn = aws_kinesis_stream.guardduty_stream.arn
    role_arn        = var.cloudwatch_kinesis_role_arn

    depends_on = [
      aws_cloudwatch_log_group.guardduty_logs,
      aws_kinesis_stream.guardduty_stream,
    ]
  }

# =========================================
# EventBridge Rule for GuardDuty Findings
# =========================================
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "${var.project_name}-guardduty-findings"
  description = "Capture GuardDuty findings"
  
  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      type = [{
        "exists": true
      }]
    }
  })
  
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-guardduty-findings"
    Component = "Security"
    Service   = "EventBridge"
  })
}

# EventBridge Target - CloudWatch Logs
resource "aws_cloudwatch_event_target" "guardduty_to_logs" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "GuardDutyToCloudWatchLogs"
  arn       = aws_cloudwatch_log_group.guardduty_logs.arn
  
  depends_on = [aws_cloudwatch_log_group.guardduty_logs]
}

# CloudWatch Logs Resource Policy for EventBridge
resource "aws_cloudwatch_log_resource_policy" "guardduty_logs_policy" {
  policy_name = "${var.project_name}-guardduty-logs-policy"
  
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
        Resource = "${aws_cloudwatch_log_group.guardduty_logs.arn}:*"
      }
    ]
  })
}