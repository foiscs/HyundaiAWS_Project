# =========================================
# Bootstrap Outputs
# =========================================
# Bootstrap 과정에서 생성된 리소스 정보 출력
# 메인 인프라에서 backend 설정 시 필요한 정보들

output "terraform_state_bucket_name" {
  description = "Terraform state 저장용 S3 버킷 이름"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "terraform_state_bucket_arn" {
  description = "Terraform state 저장용 S3 버킷 ARN"
  value       = aws_s3_bucket.terraform_state.arn
}

output "terraform_lock_table_name" {
  description = "Terraform state 잠금용 DynamoDB 테이블 이름"
  value       = aws_dynamodb_table.terraform_lock.name
}

output "terraform_lock_table_arn" {
  description = "Terraform state 잠금용 DynamoDB 테이블 ARN"
  value       = aws_dynamodb_table.terraform_lock.arn
}

output "kms_key_id" {
  description = "Terraform state 암호화용 KMS 키 ID"
  value       = aws_kms_key.terraform_state.key_id
}

output "kms_key_arn" {
  description = "Terraform state 암호화용 KMS 키 ARN"
  value       = aws_kms_key.terraform_state.arn
}

output "kms_alias_name" {
  description = "KMS 키 별칭"
  value       = aws_kms_alias.terraform_state.name
}

output "aws_region" {
  description = "AWS 리전"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "AWS 계정 ID"
  value       = data.aws_caller_identity.current.account_id
}

# =========================================
# Backend Configuration Template
# =========================================
output "backend_configuration" {
  description = "메인 인프라에서 사용할 backend 설정 템플릿"
  value = {
    backend = "s3"
    config = {
      bucket         = aws_s3_bucket.terraform_state.bucket
      key            = "infrastructure/terraform.tfstate"  # 메인 인프라용 키
      region         = var.aws_region
      encrypt        = true
      dynamodb_table = aws_dynamodb_table.terraform_lock.name
      kms_key_id     = aws_kms_key.terraform_state.key_id
    }
  }
}

# =========================================
# Instructions for Next Steps
# =========================================
output "next_steps" {
  description = "다음 단계 안내"
  value = <<-EOT
    🎉 Bootstrap 완료!
    
    📋 다음 단계:
    1. 메인 인프라의 providers.tf에 다음 backend 설정을 추가하세요:
    
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.bucket}"
        key            = "infrastructure/terraform.tfstate"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_lock.name}"
        kms_key_id     = "${aws_kms_key.terraform_state.key_id}"
      }
    }
    
    2. 메인 인프라 디렉토리에서 terraform init 실행
    3. GitHub Actions secrets에 다음 추가:
       - AWS_ROLE_ARN_INFRA (이미 존재하는 경우 확인)
       - AWS_REGION: ${var.aws_region}
    
    📂 생성된 리소스:
    - S3 Bucket: ${aws_s3_bucket.terraform_state.bucket}
    - DynamoDB Table: ${aws_dynamodb_table.terraform_lock.name}
    - KMS Key: ${aws_kms_alias.terraform_state.name}
  EOT
}

# =========================================
# Security Information
# =========================================
output "security_info" {
  description = "보안 설정 정보"
  value = {
    s3_encryption_enabled      = true
    s3_versioning_enabled     = true
    s3_public_access_blocked  = true
    dynamodb_encryption_enabled = true
    dynamodb_point_in_time_recovery = true
    kms_key_rotation_enabled  = true
    cloudtrail_enabled        = var.enable_cloudtrail_monitoring
  }
}

# =========================================
# Cost Information
# =========================================
output "estimated_monthly_cost" {
  description = "예상 월 비용 (USD, 대략적 추정)"
  value = <<-EOT
    📊 예상 월 비용 (최소 사용량 기준):
    
    💰 S3 Storage:
    - Standard Storage (1GB): $0.023
    - Versioning (추가 1GB): $0.023
    
    💰 DynamoDB:
    - PAY_PER_REQUEST 모드: $0 (미사용 시)
    - 읽기/쓰기 요청: State 작업당 $0.000001-0.000005
    
    💰 KMS:
    - 키 유지비: $1.00
    - API 호출: 매월 20,000회 무료, 이후 $0.03/10,000회
    
    💰 CloudTrail:
    - 데이터 이벤트: $0.10/100,000 이벤트
    
    📋 총 예상 비용: $1.05-2.00/월
    
    ⚠️  주의: 실제 비용은 사용량에 따라 달라질 수 있습니다.
  EOT
}