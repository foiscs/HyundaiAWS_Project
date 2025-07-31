variable "create_blog_s3_user" {
  description = "Create blog-s3-user if it does not exist"
  type        = bool
  default     = false
}

variable "create_splunk_kinesis_reader" {
  description = "Create splunk-kinesis-reader user if it does not exist"
  type        = bool
  default     = false
}

variable "create_blog_s3_policy" {
  description = "Create blog-s3-user-policy if it does not exist"
  type        = bool
  default     = false
}

variable "create_splunk_kinesis_policy" {
  description = "Create splunk-kinesis-reader-policy if it does not exist"
  type        = bool
  default     = false
}

variable "create_cloudtrail_cloudwatch_role" {
  description = "Create CloudTrail-CloudWatchLogs-Role if it does not exist"
  type        = bool
  default     = false
}

variable "create_cloudtrail_cloudwatch_policy" {
  description = "Create CloudTrail-CloudWatchLogs-Policy if it does not exist"
  type        = bool
  default     = false
}

variable "create_cloudwatch_kinesis_role" {
  description = "Create CloutWatchLogs-Kinesis-Role if it does not exist"
  type        = bool
  default     = false
}

variable "create_cloudwatch_kinesis_policy" {
  description = "Create CloudWatchLogs-Kinesis-Policy if it does not exist"
  type        = bool
  default     = false
}

variable "create_firehose_waf_role" {
  description = "Create Firehose WAF Role if it does not exist"
  type        = bool
  default     = false
}

variable "create_firehose_waf_policy" {
  description = "Create Firehose WAF Policy if it does not exist"
  type        = bool
  default     = false
}

# 액세스 키 생성 제어 변수 (이미 있음으로 보이는데 없으면 추가)
variable "create_access_keys" {
  description = "Create access keys for users"
  type        = bool
  default     = false
}


# 추가로 사용할 변수 (예: var.project_name, var.s3_logs_bucket_name, var.common_tags 등)
variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
}

variable "s3_logs_bucket_name" {
  description = "S3 bucket name for logs"
  type        = string
}

variable "common_tags" {
  description = "Common tags applied to resources"
  type        = map(string)
  default     = {}
}
