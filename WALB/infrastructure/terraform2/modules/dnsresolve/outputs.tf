  output "route53_query_log_id" {
    description = "Route 53 Query Log configuration ID"
    value       = aws_route53_query_log.main.id
  }

  output "route53_query_log_arn" {
    description = "Route 53 Query Log ARN"
    value       = aws_route53_query_log.main.arn
  }

  output "dns_logs_s3_prefix" {
    description = "S3 prefix for DNS query logs"
    value       = "dns-query-logs/"
  }