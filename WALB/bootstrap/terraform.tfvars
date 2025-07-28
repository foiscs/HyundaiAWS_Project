# =========================================
# Bootstrap Terraform Variables
# =========================================
# Bootstrap 실행을 위한 변수 값 설정

# 기본 설정
aws_region   = "ap-northeast-2"
project_name = "WALB"
owner        = "DevSecOps Team"
cost_center  = "Infrastructure"

# 보안 설정
enable_kms_encryption        = true
enable_cloudtrail_monitoring = false  # CloudTrail 비활성화 (S3 정책 충돌 방지)
enable_access_logging        = true
enable_mfa_requirement       = false  # 필요시 true로 변경

# 라이프사이클 설정
state_bucket_lifecycle_days = 90
log_retention_days          = 90

# 추가 태그
additional_tags = {
  Department    = "IT"
  Application   = "Infrastructure"
  Backup        = "Required"
  Monitoring    = "Enabled"
  Compliance    = "ISMS-P"
  DataClass     = "Internal"
}

# GitHub Actions 역할 ARN (메인 인프라에서 생성된 후 추가)
# allowed_principals = [
#   "arn:aws:iam::ACCOUNT-ID:role/WALB-app-github-actions-infra-role"
# ]