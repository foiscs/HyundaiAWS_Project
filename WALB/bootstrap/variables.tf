# =========================================
# Bootstrap Variables
# =========================================
# Terraform Backend 리소스 생성을 위한 변수 정의

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
  
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS 리전 형식이 올바르지 않습니다. (예: ap-northeast-2)"
  }
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "WALB"
  
  validation {
    condition = can(regex("^[A-Z][A-Z0-9-]*$", var.project_name))
    error_message = "프로젝트 이름은 대문자로 시작하고 대문자, 숫자, 하이픈만 포함해야 합니다."
  }
}

variable "owner" {
  description = "리소스 소유자"
  type        = string
  default     = "DevSecOps Team"
}

variable "cost_center" {
  description = "비용 센터"
  type        = string
  default     = "Infrastructure"
}

variable "enable_kms_encryption" {
  description = "KMS 암호화 활성화 여부"
  type        = bool
  default     = true
}

variable "enable_cloudtrail_monitoring" {
  description = "CloudTrail 모니터링 활성화 여부"
  type        = bool
  default     = true
}

variable "state_bucket_lifecycle_days" {
  description = "State 파일 이전 버전 보관 일수"
  type        = number
  default     = 90
  
  validation {
    condition = var.state_bucket_lifecycle_days >= 30 && var.state_bucket_lifecycle_days <= 365
    error_message = "라이프사이클 일수는 30일에서 365일 사이여야 합니다."
  }
}

variable "log_retention_days" {
  description = "CloudWatch 로그 보관 일수"
  type        = number
  default     = 90
  
  validation {
    condition = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "유효한 로그 보관 일수를 선택하세요."
  }
}

variable "additional_tags" {
  description = "추가 태그"
  type        = map(string)
  default     = {}
}

# =========================================
# Security Variables
# =========================================
variable "allowed_principals" {
  description = "Terraform state에 접근할 수 있는 IAM 역할/사용자 ARN 목록"
  type        = list(string)
  default     = []
}

variable "enable_mfa_requirement" {
  description = "MFA 요구사항 활성화 (고보안 환경용)"
  type        = bool
  default     = false
}

variable "enable_access_logging" {
  description = "S3 접근 로깅 활성화"
  type        = bool
  default     = true
}