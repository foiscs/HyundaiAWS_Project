# ========================================
# Security Hub Module Variables
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
# Security Hub Configuration
# ========================================

variable "enable_default_standards" {
  description = "Enable default Security Hub standards"
  type        = bool
  default     = true
}

variable "enable_aws_foundational" {
  description = "Enable AWS Foundational Security Best Practices standard"
  type        = bool
  default     = true
}

variable "enable_cis_standard" {
  description = "Enable CIS AWS Foundations Benchmark standard"
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
  description = "Enable CloudWatch monitoring for Security Hub"
  type        = bool
  default     = true
}

variable "severity_levels" {
  description = "Security Hub finding severity levels to capture"
  type        = list(string)
  default     = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
}