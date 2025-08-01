# ========================================
# WAF Module Outputs
# ========================================

# WAF Web ACL
output "web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.arn
}

output "web_acl_name" {
  description = "Name of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.name
}

output "web_acl_capacity" {
  description = "Capacity units consumed by the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.capacity
}

# WAF IP Set
output "blocked_ip_set_id" {
  description = "ID of the WAF IP Set for blocked IPs"
  value       = length(var.blocked_ip_addresses) > 0 ? aws_wafv2_ip_set.blocked_ips[0].id : null
}

output "blocked_ip_set_arn" {
  description = "ARN of the WAF IP Set for blocked IPs"
  value       = length(var.blocked_ip_addresses) > 0 ? aws_wafv2_ip_set.blocked_ips[0].arn : null
}

# WAF Association
output "alb_association_id" {
  description = "ID of the WAF-ALB association"
  value       = var.target_alb_name != "" ? aws_wafv2_web_acl_association.alb_association[0].id : null
}

output "associated_alb_arn" {
  description = "ARN of the ALB associated with WAF"
  value       = var.target_alb_name != "" ? aws_wafv2_web_acl_association.alb_association[0].resource_arn : null
}

# Kinesis Firehose
output "firehose_delivery_stream_name" {
  description = "Name of the Kinesis Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.waf_logs.name
}

output "firehose_delivery_stream_arn" {
  description = "ARN of the Kinesis Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.waf_logs.arn
}

output "firehose_destination_id" {
  description = "Destination ID of the Kinesis Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.waf_logs.destination_id
}

# CloudWatch Log Group
output "firehose_log_group_name" {
  description = "Name of the CloudWatch log group for Firehose"
  value       = aws_cloudwatch_log_group.firehose_logs.name
}

output "firehose_log_group_arn" {
  description = "ARN of the CloudWatch log group for Firehose"
  value       = aws_cloudwatch_log_group.firehose_logs.arn
}

output "firehose_log_stream_name" {
  description = "Name of the CloudWatch log stream for Firehose"
  value       = aws_cloudwatch_log_stream.firehose_s3_delivery.name
}

# WAF Logging Configuration
output "waf_logging_configuration_id" {
  description = "ID of the WAF logging configuration"
  value       = aws_wafv2_web_acl_logging_configuration.main.id
}

# WAF Configuration Summary
output "waf_info" {
  description = "Summary of WAF configuration"
  value = {
    web_acl_id              = aws_wafv2_web_acl.main.id
    web_acl_arn             = aws_wafv2_web_acl.main.arn
    web_acl_name            = aws_wafv2_web_acl.main.name
    web_acl_capacity        = aws_wafv2_web_acl.main.capacity
    firehose_stream_name    = aws_kinesis_firehose_delivery_stream.waf_logs.name
    log_group_name          = aws_cloudwatch_log_group.firehose_logs.name
    associated_alb          = var.target_alb_name
    rate_limit              = var.rate_limit
    blocked_ips_count       = length(var.blocked_ip_addresses)
    rules_enabled = {
      common_rule_set       = true
      known_bad_inputs      = true
      rate_limiting         = true
      ip_blocking           = length(var.blocked_ip_addresses) > 0
    }
    monitoring_enabled      = var.enable_monitoring
    data_transformation     = var.enable_data_transformation
  }
}