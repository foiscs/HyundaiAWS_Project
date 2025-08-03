# ========================================
# GuardDuty Module Outputs
# ========================================

# GuardDuty Detector
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = aws_guardduty_detector.main.id
}

output "guardduty_detector_arn" {
  description = "ARN of the GuardDuty detector"
  value       = aws_guardduty_detector.main.arn
}

output "guardduty_account_id" {
  description = "AWS account ID where GuardDuty is enabled"
  value       = aws_guardduty_detector.main.account_id
}

# Publishing Destination
output "publishing_destination_id" {
  description = "ID of the GuardDuty publishing destination"
  value       = aws_guardduty_publishing_destination.cloudwatch_logs.id
}

output "publishing_destination_arn" {
  description = "ARN of the GuardDuty publishing destination"
  value       = aws_guardduty_publishing_destination.cloudwatch_logs.destination_arn
}

# CloudWatch Log Group
output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for GuardDuty"
  value       = aws_cloudwatch_log_group.guardduty_logs.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for GuardDuty"
  value       = aws_cloudwatch_log_group.guardduty_logs.name
}

# Kinesis Stream
output "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream for GuardDuty findings"
  value       = aws_kinesis_stream.guardduty_stream.arn
}

output "kinesis_stream_name" {
  description = "Name of the Kinesis stream for GuardDuty findings"
  value       = aws_kinesis_stream.guardduty_stream.name
}

output "kinesis_stream_shard_count" {
  description = "Number of shards in the Kinesis stream"
  value       = aws_kinesis_stream.guardduty_stream.shard_count
}

# Subscription Filter
output "subscription_filter_name" {
  description = "Name of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.guardduty_kinesis.name
}

output "subscription_filter_destination_arn" {
  description = "Destination ARN of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.guardduty_kinesis.destination_arn
}

# GuardDuty Configuration Summary
output "guardduty_info" {
  description = "Summary of GuardDuty configuration"
  value = {
    detector_id               = aws_guardduty_detector.main.id
    detector_arn             = aws_guardduty_detector.main.arn
    account_id               = aws_guardduty_detector.main.account_id
    finding_publishing_frequency = aws_guardduty_detector.main.finding_publishing_frequency
    log_group_name           = aws_cloudwatch_log_group.guardduty_logs.name
    kinesis_stream_name      = aws_kinesis_stream.guardduty_stream.name
    subscription_filter_name = aws_cloudwatch_log_subscription_filter.guardduty_kinesis.name
    data_sources = {
      s3_protection         = var.enable_s3_protection
      kubernetes_protection = var.enable_kubernetes_protection
      malware_protection    = var.enable_malware_protection
    }
    monitoring_enabled = var.enable_monitoring
  }
}