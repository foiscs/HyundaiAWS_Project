# ========================================
# GuardDuty Module Variables
# ========================================

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "cloudwatch_kinesis_role_arn" {
  description = "ARN of the IAM role for CloudWatch Logs to Kinesis"
  type        = string
}

variable "kms_key_arn" {
  description = "ARN of the KMS key for encryption"
  type        = string
}

variable "s3_logs_bucket_arn" {
  description = "ARN of the S3 bucket for logs"
  type        = string
}

variable "sns_topic_arn" {
  description = "ARN of the SNS topic for notifications"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ========================================
# GuardDuty Configuration
# ========================================

variable "finding_publishing_frequency" {
  description = "Frequency of GuardDuty finding publishing"
  type        = string
  default     = "FIFTEEN_MINUTES"
  validation {
    condition = contains([
      "FIFTEEN_MINUTES",
      "ONE_HOUR", 
      "SIX_HOURS"
    ], var.finding_publishing_frequency)
    error_message = "Finding publishing frequency must be one of: FIFTEEN_MINUTES, ONE_HOUR, SIX_HOURS."
  }
}

variable "enable_s3_protection" {
  description = "Enable S3 protection in GuardDuty"
  type        = bool
  default     = true
}

variable "enable_kubernetes_protection" {
  description = "Enable Kubernetes audit logs protection in GuardDuty"
  type        = bool
  default     = true
}

variable "enable_malware_protection" {
  description = "Enable malware protection for EC2 instances in GuardDuty"
  type        = bool
  default     = true
}

# ========================================
# CloudWatch and Kinesis Configuration
# ========================================

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 90
}

variable "kinesis_shard_count" {
  description = "Number of shards for Kinesis stream"
  type        = number
  default     = 1
}

variable "kinesis_retention_hours" {
  description = "Number of hours to retain data in Kinesis stream"
  type        = number
  default     = 24
}

variable "log_filter_pattern" {
  description = "Filter pattern for CloudWatch logs subscription"
  type        = string
  default     = ""
}

# ========================================
# Monitoring Configuration
# ========================================

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring for GuardDuty"
  type        = bool
  default     = true
}

variable "high_severity_threshold" {
  description = "Threshold for high severity findings to trigger alerts"
  type        = number
  default     = 3
}