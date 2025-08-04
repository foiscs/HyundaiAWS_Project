  # ========================================
  # DNS Resolve Module Variables
  # ========================================

  variable "project_name" {
    description = "Name of the project"
    type        = string
  }

  variable "environment" {
    description = "Environment name (dev, staging, prod)"
    type        = string
  }

  variable "hosted_zone_id" {
    description = "Route 53 Hosted Zone ID for DNS query logging"
    type        = string
  }

  variable "s3_logs_bucket_name" {
    description = "Name of the S3 bucket for storing DNS query logs"
    type        = string
  }

  variable "vpc_id" {
    description = "VPC ID for DNS resolver configuration"
    type        = string
  }

  variable "firehose_role_arn" {
    description = "ARN of the IAM role for Kinesis Data Firehose"
    type        = string
  }

  variable "cloudwatch_kinesis_role_arn" {
    description = "ARN of the IAM role for CloudWatch Logs to Kinesis"
    type        = string
  }

  variable "common_tags" {
    description = "Common tags to apply to all resources"
    type        = map(string)
    default     = {}
  }

  # ========================================
  # S3 Lifecycle Configuration
  # ========================================

  variable "enable_s3_lifecycle" {
    description = "Enable S3 lifecycle management for DNS logs"
    type        = bool
    default     = true
  }

  variable "transition_to_ia_days" {
    description = "Days to transition to Standard-IA"
    type        = number
    default     = 30
  }

  variable "transition_to_glacier_days" {
    description = "Days to transition to Glacier"
    type        = number
    default     = 90
  }

  variable "transition_to_deep_archive_days" {
    description = "Days to transition to Deep Archive"
    type        = number
    default     = 365
  }

  variable "dns_log_retention_days" {
    description = "Days to retain DNS logs before deletion"
    type        = number
    default     = 2555  # 7 years for compliance
  }