  # ========================================
  # DNS Resolve Module Outputs
  # ========================================

  # Route 53 Resolver Query Log Config
  output "resolver_query_log_config_id" {
    description = "Route 53 Resolver Query Log configuration ID"
    value       = aws_route53_resolver_query_log_config.main.id
  }

  output "resolver_query_log_config_arn" {
    description = "Route 53 Resolver Query Log configuration ARN"
    value       = aws_route53_resolver_query_log_config.main.arn
  }

  # Query Log Config Association
  output "query_log_association_id" {
    description = "Route 53 Resolver Query Log Config Association ID"
    value       = aws_route53_resolver_query_log_config_association.main.id
  }

  # S3 Configuration
  output "dns_logs_s3_prefix" {
    description = "S3 prefix for DNS query logs"
    value       = "dns-query-logs/"
  }

  output "s3_destination_arn" {
    description = "S3 destination ARN for DNS query logs"
    value       = "arn:aws:s3:::${var.s3_logs_bucket_name}/dns-query-logs/"
  }

  # Configuration Summary
  output "dns_logging_info" {
    description = "Summary of DNS logging configuration"
    value = {
      resolver_config_id      = aws_route53_resolver_query_log_config.main.id
      resolver_config_arn     = aws_route53_resolver_query_log_config.main.arn
      association_id          = aws_route53_resolver_query_log_config_association.main.id
      vpc_id                  = var.vpc_id
      s3_destination          = "arn:aws:s3:::${var.s3_logs_bucket_name}/dns-query-logs/"
      s3_logs_prefix          = "dns-query-logs/"
      retention_days          = var.dns_log_retention_days
      lifecycle_enabled       = var.enable_s3_lifecycle
    }
  }