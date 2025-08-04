# ========================================
# Security Hub Module Outputs
# ========================================

# Security Hub Account
output "security_hub_account_id" {
  description = "Security Hub account ID"
  value       = aws_securityhub_account.main.id
}

# Standards Subscriptions
output "aws_foundational_standard_arn" {
  description = "ARN of AWS Foundational Security Best Practices standard subscription"
  value       = var.enable_aws_foundational ? aws_securityhub_standards_subscription.aws_foundational[0].standards_arn : null
}

output "cis_standard_arn" {
  description = "ARN of CIS AWS Foundations Benchmark standard subscription"
  value       = var.enable_cis_standard ? aws_securityhub_standards_subscription.cis[0].standards_arn : null
}

# CloudWatch Log Group
output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for Security Hub"
  value       = aws_cloudwatch_log_group.security_hub_logs.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for Security Hub"
  value       = aws_cloudwatch_log_group.security_hub_logs.name
}

# Kinesis Stream
output "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream for Security Hub findings"
  value       = aws_kinesis_stream.security_hub_stream.arn
}

output "kinesis_stream_name" {
  description = "Name of the Kinesis stream for Security Hub findings"
  value       = aws_kinesis_stream.security_hub_stream.name
}

output "kinesis_stream_shard_count" {
  description = "Number of shards in the Kinesis stream"
  value       = aws_kinesis_stream.security_hub_stream.shard_count
}

# EventBridge Rule
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for Security Hub findings"
  value       = aws_cloudwatch_event_rule.security_hub_findings.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule for Security Hub findings"
  value       = aws_cloudwatch_event_rule.security_hub_findings.name
}

# Subscription Filter
output "subscription_filter_name" {
  description = "Name of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.security_hub_kinesis.name
}

output "subscription_filter_destination_arn" {
  description = "Destination ARN of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.security_hub_kinesis.destination_arn
}

# Summary
output "security_hub_info" {
  description = "Summary of Security Hub configuration"
  value = {
    account_id                = aws_securityhub_account.main.id
    log_group_name           = aws_cloudwatch_log_group.security_hub_logs.name
    kinesis_stream_name      = aws_kinesis_stream.security_hub_stream.name
    eventbridge_rule_name    = aws_cloudwatch_event_rule.security_hub_findings.name
    subscription_filter_name = aws_cloudwatch_log_subscription_filter.security_hub_kinesis.name
    standards_enabled = {
      default_standards    = var.enable_default_standards
      aws_foundational    = var.enable_aws_foundational
      cis_benchmark       = var.enable_cis_standard
    }
    monitoring_enabled = var.enable_monitoring
  }
}