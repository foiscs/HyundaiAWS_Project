# ========================================
# VPC Flow Logs Module Variables
# ========================================

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC to enable flow logs for"
  type        = string
}

variable "vpc_flow_logs_s3_arn" {
  description = "ARN of the S3 bucket for storing VPC flow logs"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for lifecycle configuration"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# ========================================
# VPC Flow Logs Configuration
# ========================================

variable "traffic_type" {
  description = "Type of traffic to log (ALL, ACCEPT, REJECT)"
  type        = string
  default     = "ALL"
  validation {
    condition = contains([
      "ALL",
      "ACCEPT", 
      "REJECT"
    ], var.traffic_type)
    error_message = "Traffic type must be one of: ALL, ACCEPT, REJECT."
  }
}

variable "vpc_flow_logs_format" {
  description = "Custom format for VPC flow logs"
  type        = string
  default     = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${windowstart} $${windowend} $${action} $${flowlogstatus}"
}

# ========================================
# S3 Destination Options
# ========================================

variable "enable_hive_partitions" {
  description = "Enable Hive-compatible partitions for S3"
  type        = bool
  default     = false
}

variable "enable_hourly_partitions" {
  description = "Enable per-hour partitions for S3"
  type        = bool
  default     = true
}

# ========================================
# S3 Lifecycle Configuration
# ========================================

variable "enable_s3_lifecycle" {
  description = "Enable S3 lifecycle policy for VPC flow logs"
  type        = bool
  default     = true
}

variable "vpc_flow_logs_retention_days" {
  description = "Number of days to retain VPC flow logs before deletion"
  type        = number
  default     = 365
}

variable "transition_to_ia_days" {
  description = "Number of days before transitioning to Standard-IA"
  type        = number
  default     = 30
}

variable "transition_to_glacier_days" {
  description = "Number of days before transitioning to Glacier"
  type        = number
  default     = 90
}

variable "transition_to_deep_archive_days" {
  description = "Number of days before transitioning to Deep Archive"
  type        = number
  default     = 180
}