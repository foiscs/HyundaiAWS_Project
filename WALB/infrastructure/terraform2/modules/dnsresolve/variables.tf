  # S3 Lifecycle Configuration
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