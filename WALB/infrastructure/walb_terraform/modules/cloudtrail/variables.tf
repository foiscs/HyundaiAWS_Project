# ========================================
# CloudTrail Module Variables
# ========================================

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for CloudTrail logs"
  type        = string
}

variable "cloudtrail_cloudwatch_role_arn" {
  description = "ARN of the IAM role for CloudTrail to CloudWatch Logs"
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

# ========================================
# CloudTrail Configuration
# ========================================

variable "enable_data_events" {
  description = "Enable data events for CloudTrail"
  type        = bool
  default     = true
}

variable "enable_insights" {
  description = "Enable CloudTrail insights"
  type        = bool
  default     = false
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring for CloudTrail"
  type        = bool
  default     = true
}

variable "log_filter_pattern" {
  description = "Filter pattern for CloudWatch logs subscription"
  type        = string
  default     = ""
}