# ========================================
# WAF Module Variables
# ========================================

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "target_alb_name" {
  description = "Name of the target ALB to associate with WAF"
  type        = string
  default     = ""
}

variable "firehose_role_arn" {
  description = "ARN of the IAM role for Firehose to deliver logs to S3"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for storing WAF logs"
  type        = string
}

variable "kms_key_arn" {
  description = "ARN of the KMS key for encryption"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ========================================
# WAF Configuration
# ========================================

variable "rate_limit" {
  description = "Rate limit for requests per 5-minute period from a single IP"
  type        = number
  default     = 2000
  validation {
    condition     = var.rate_limit >= 100 && var.rate_limit <= 20000000
    error_message = "Rate limit must be between 100 and 20,000,000."
  }
}

variable "blocked_ip_addresses" {
  description = "List of IP addresses/CIDR blocks to block"
  type        = list(string)
  default     = []
}

variable "blocked_requests_threshold" {
  description = "Threshold for blocked requests to trigger alerts"
  type        = number
  default     = 100
}

# ========================================
# Firehose Configuration
# ========================================

variable "buffer_size_mb" {
  description = "Size of the buffer (in MB) that Firehose uses for incoming data"
  type        = number
  default     = 5
  validation {
    condition     = var.buffer_size_mb >= 1 && var.buffer_size_mb <= 128
    error_message = "Buffer size must be between 1 and 128 MB."
  }
}

variable "buffer_interval_seconds" {
  description = "Buffer interval (in seconds) for Firehose"
  type        = number
  default     = 300
  validation {
    condition     = var.buffer_interval_seconds >= 60 && var.buffer_interval_seconds <= 900
    error_message = "Buffer interval must be between 60 and 900 seconds."
  }
}

# ========================================
# Monitoring and Logging Configuration
# ========================================

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring for WAF"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 90
}

# ========================================
# Data Transformation Configuration
# ========================================

variable "enable_data_transformation" {
  description = "Enable data transformation using Lambda"
  type        = bool
  default     = false
}

variable "lambda_processor_arn" {
  description = "ARN of the Lambda function for data transformation"
  type        = string
  default     = null
}