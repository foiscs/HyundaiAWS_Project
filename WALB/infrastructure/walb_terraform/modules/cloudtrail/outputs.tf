# ========================================
# CloudTrail Module Outputs
# ========================================

# CloudTrail
output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = aws_cloudtrail.main.arn
}

output "cloudtrail_name" {
  description = "Name of the CloudTrail"
  value       = aws_cloudtrail.main.name
}

output "cloudtrail_id" {
  description = "ID of the CloudTrail"
  value       = aws_cloudtrail.main.id
}

output "cloudtrail_home_region" {
  description = "Home region of the CloudTrail"
  value       = aws_cloudtrail.main.home_region
}

# CloudWatch Log Group
output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for CloudTrail"
  value       = aws_cloudwatch_log_group.cloudtrail_logs.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for CloudTrail"
  value       = aws_cloudwatch_log_group.cloudtrail_logs.name
}

# Kinesis Stream
output "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream for CloudTrail logs"
  value       = aws_kinesis_stream.cloudtrail_stream.arn
}

output "kinesis_stream_name" {
  description = "Name of the Kinesis stream for CloudTrail logs"
  value       = aws_kinesis_stream.cloudtrail_stream.name
}

output "kinesis_stream_shard_count" {
  description = "Number of shards in the Kinesis stream"
  value       = aws_kinesis_stream.cloudtrail_stream.shard_count
}

# Subscription Filter
output "subscription_filter_name" {
  description = "Name of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.cloudtrail_kinesis.name
}

output "subscription_filter_destination_arn" {
  description = "Destination ARN of the CloudWatch logs subscription filter"
  value       = aws_cloudwatch_log_subscription_filter.cloudtrail_kinesis.destination_arn
}

# Summary
output "cloudtrail_info" {
  description = "Summary of CloudTrail configuration"
  value = {
    cloudtrail_name           = aws_cloudtrail.main.name
    cloudtrail_arn           = aws_cloudtrail.main.arn
    log_group_name           = aws_cloudwatch_log_group.cloudtrail_logs.name
    kinesis_stream_name      = aws_kinesis_stream.cloudtrail_stream.name
    subscription_filter_name = aws_cloudwatch_log_subscription_filter.cloudtrail_kinesis.name
    multi_region_trail       = aws_cloudtrail.main.is_multi_region_trail
    logging_enabled          = aws_cloudtrail.main.enable_logging
  }
}