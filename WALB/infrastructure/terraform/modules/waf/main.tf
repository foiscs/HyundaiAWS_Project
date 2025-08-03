data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
  # ALB 정보 가져오기
data "aws_lb" "target_alb" {
  count = var.target_alb_name != "" ? 1 : 0
  name  = var.target_alb_name
}

resource "aws_wafv2_web_acl" "main" {
  name  = "${var.project_name}-web-acl"
  scope = "REGIONAL"  # ALB는 REGIONAL scope 사용
  default_action {
    allow {}
  }
  # AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }
  # AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }
  # Rate Limiting Rule
  rule {
    name     = "RateLimitRule"
    priority = 3
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }
  # Custom IP Block Rule
  dynamic "rule" {
    for_each = length(var.blocked_ip_addresses) > 0 ? [1] : []
    content {
      name     = "BlockedIPsRule"
      priority = 4
      action {
        block {}
      }
      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.blocked_ips[0].arn
        }
      }
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "BlockedIPsRule"
        sampled_requests_enabled   = true
      }
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}WebACL"
    sampled_requests_enabled   = true
  }
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-web-acl"
    Component = "Security"
    Service   = "WAF"
  })
}

# WAF IP Set for Blocked IPs
resource "aws_wafv2_ip_set" "blocked_ips" {
  count = length(var.blocked_ip_addresses) > 0 ? 1 : 0
  name               = "${var.project_name}-blocked-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.blocked_ip_addresses
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-blocked-ips"
    Component = "Security"
    Service   = "WAF"
  })
}

# WAF와 ALB 연결
resource "aws_wafv2_web_acl_association" "alb_association" {
  count = var.target_alb_name != "" ? 1 : 0
  resource_arn = data.aws_lb.target_alb[0].arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
  depends_on = [aws_wafv2_web_acl.main]
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_kinesis_firehose_delivery_stream.waf_logs.arn]
  # Filter sensitive fields
  redacted_fields {
    single_header {
      name = "authorization"
    }
  }
  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
  depends_on = [aws_kinesis_firehose_delivery_stream.waf_logs]
}

# =========================================
# Kinesis Data Firehose for WAF Logs
# =========================================
resource "aws_kinesis_firehose_delivery_stream" "waf_logs" {
  name        = "aws-waf-logs-${var.project_name}"  # WAF 로그는 "aws-waf-logs-" prefix 필수
  destination = "extended_s3"
  extended_s3_configuration {
    role_arn   = var.firehose_role_arn
    bucket_arn = var.s3_bucket_arn
    # S3 Path Configuration
    prefix              = "waf-logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "waf-logs-errors/"
    # Buffering Configuration
    buffering_size     = var.buffer_size_mb
    buffering_interval = var.buffer_interval_seconds
    # Compression
    compression_format = "GZIP"
    # CloudWatch Logging
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_logs.name
      log_stream_name = "S3Delivery"
    }
    # Data Transformation (Optional)
    dynamic "processing_configuration" {
      for_each = var.enable_data_transformation ? [1] : []
      content {
        enabled = true
        processors {
          type = "Lambda"
          parameters {
            parameter_name  = "LambdaArn"
            parameter_value = var.lambda_processor_arn
          }
        }
      }
    }
  }
  tags = merge(var.common_tags, {
    Name      = "aws-waf-logs-${var.project_name}"
    Component = "Security"
    Service   = "Firehose"
    Purpose   = "WAF Logs Delivery"
  })
}

# CloudWatch Log Group for Firehose
resource "aws_cloudwatch_log_group" "firehose_logs" {
  name              = "/aws/kinesisfirehose/aws-waf-logs-${var.project_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-firehose-logs"
    Component = "Security"
    Service   = "Firehose"
  })
}
# CloudWatch Log Stream for Firehose
resource "aws_cloudwatch_log_stream" "firehose_s3_delivery" {
  name           = "S3Delivery"
  log_group_name = aws_cloudwatch_log_group.firehose_logs.name
}