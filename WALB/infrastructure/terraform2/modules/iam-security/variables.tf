variable "project_name" {
  type        = string
  description = "Name of the project"
}

variable "common_tags" {
  type        = map(string)
  description = "Common tags to be applied to all resources"
  default     = {}
}

variable "s3_logs_bucket_name" {
  type        = string
  description = "Name of the S3 logs bucket where security logs are stored"
}

variable "create_access_keys" {
  type        = bool
  description = "Whether to create access keys for the users"
  default     = false
}