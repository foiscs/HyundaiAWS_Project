# ========================================
# VPC Flow Logs Module Outputs
# ========================================

# VPC Flow Log
output "flow_log_id" {
  description = "ID of the VPC flow log"
  value       = aws_flow_log.vpc_flow_logs.id
}

output "flow_log_arn" {
  description = "ARN of the VPC flow log"
  value       = aws_flow_log.vpc_flow_logs.arn
}

output "flow_log_traffic_type" {
  description = "Traffic type of the VPC flow log"
  value       = aws_flow_log.vpc_flow_logs.traffic_type
}

output "flow_log_destination_arn" {
  description = "ARN of the destination for VPC flow log"
  value       = aws_flow_log.vpc_flow_logs.log_destination
}

output "flow_log_destination_type" {
  description = "Type of the destination for VPC flow log"
  value       = aws_flow_log.vpc_flow_logs.log_destination_type
}

# S3 Lifecycle Configuration
output "s3_lifecycle_configuration_bucket" {
  description = "Bucket name of the S3 lifecycle configuration for VPC flow logs"
  value       = var.enable_s3_lifecycle ? aws_s3_bucket_lifecycle_configuration.vpc_flow_logs_lifecycle[0].bucket : null
}

# VPC Flow Logs Configuration Summary
output "vpc_flow_logs_info" {
  description = "Summary of VPC flow logs configuration"
  value = {
    flow_log_id           = aws_flow_log.vpc_flow_logs.id
    flow_log_arn          = aws_flow_log.vpc_flow_logs.arn
    vpc_id                = var.vpc_id
    traffic_type          = var.traffic_type
    destination_type      = aws_flow_log.vpc_flow_logs.log_destination_type
    destination_s3_arn    = var.vpc_flow_logs_s3_arn
    log_format            = var.vpc_flow_logs_format
    partitioning = {
      hive_compatible     = var.enable_hive_partitions
      hourly_partitions   = var.enable_hourly_partitions
    }
    lifecycle_policy = {
      enabled             = var.enable_s3_lifecycle
      retention_days      = var.vpc_flow_logs_retention_days
      ia_transition_days  = var.transition_to_ia_days
      glacier_transition_days = var.transition_to_glacier_days
      deep_archive_transition_days = var.transition_to_deep_archive_days
    }
  }
}