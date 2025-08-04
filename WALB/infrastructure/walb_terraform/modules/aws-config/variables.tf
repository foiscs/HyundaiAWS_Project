# =========================================
# AWS Config Module Variables
# =========================================

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "s3_logs_bucket_name" {
  description = "S3 bucket name for AWS Config logs"
  type        = string
}

variable "record_all_resources" {
  description = "Whether to record all supported resource types"
  type        = bool
  default     = true
}

variable "include_global_resources" {
  description = "Whether to include global resources (IAM, Route53, etc.)"
  type        = bool
  default     = true
}

variable "specific_resource_types" {
  description = "List of specific resource types to record (used when record_all_resources is false)"
  type        = list(string)
  default     = []
}

variable "enable_config_rules" {
  description = "Whether to enable AWS Config Rules"
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}