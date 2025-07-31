  data "aws_caller_identity" "current" {}
  data "aws_region" "current" {}

  # Route 53 Query Logging Configuration (Direct to S3)
  resource "aws_route53_query_log" "main" {
    destination_arn = "arn:aws:s3:::${var.s3_logs_bucket_name}/dns-query-logs/"
    zone_id         = var.hosted_zone_id
    
    tags = merge(var.common_tags, {
      Name      = "${var.project_name}-dns-query-logging"
      Component = "Security"
      Service   = "Route53"
      Purpose   = "DNS Query Analysis"
    })
  }
  # S3 prefix for DNS logs organization
  resource "aws_s3_object" "dns_logs_prefix" {
    bucket = var.s3_logs_bucket_name
    key    = "dns-query-logs/"
    
    tags = merge(var.common_tags, {
      Name      = "${var.project_name}-dns-logs-prefix"
      Component = "Security"
      Purpose   = "DNS Logs Organization"
    })
  }
  
  # =========================================
  # S3 Lifecycle Management for DNS Logs
  # =========================================

  resource "aws_s3_bucket_lifecycle_configuration" "dns_logs_lifecycle" {
    count  = var.enable_s3_lifecycle ? 1 : 0
    bucket = var.s3_logs_bucket_name
    
    rule {
      id     = "dns-logs-lifecycle"
      status = "Enabled"
      
      filter {
        prefix = "dns-query-logs/"
      }
      
      transition {
        days          = var.transition_to_ia_days
        storage_class = "STANDARD_IA"
      }

      transition {
        days          = var.transition_to_glacier_days
        storage_class = "GLACIER"
      }

      transition {
        days          = var.transition_to_deep_archive_days
        storage_class = "DEEP_ARCHIVE"
      }

      expiration {
        days = var.dns_log_retention_days
      }
    }
  }