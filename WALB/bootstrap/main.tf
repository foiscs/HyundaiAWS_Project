# =========================================
# Terraform Backend Bootstrap Resources
# =========================================
# S3 버킷과 DynamoDB 테이블만 생성하는 bootstrap 구성
# 이 파일들은 로컬 state로 관리되며, 메인 인프라는 여기서 생성한 리소스를 backend로 사용

# 현재 AWS 계정 정보 조회
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# 고유 접미사 생성 (계정 ID 뒤 4자리 사용)
locals {
  account_suffix = substr(data.aws_caller_identity.current.account_id, -4, 4)
  bucket_name    = "walb-terraform-state-${local.account_suffix}"
  table_name     = "walb-terraform-lock-${local.account_suffix}"
  
  common_tags = {
    Project       = "WALB"
    Environment   = "bootstrap"
    Purpose       = "TerraformBackend"
    ManagedBy     = "Terraform"
    Owner         = "DevSecOps Team"
    CostCenter    = "Infrastructure"
    CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
  }
}

# =========================================
# S3 Bucket for Terraform State
# =========================================
resource "aws_s3_bucket" "terraform_state" {
  bucket        = local.bucket_name
  force_destroy = false  # 실수로 삭제 방지

  tags = merge(local.common_tags, {
    Name        = local.bucket_name
    Description = "Terraform state 파일 저장용 S3 버킷"
  })

  lifecycle {
    prevent_destroy = true
  }
}

# S3 버킷 버전 관리 활성화
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 버킷 암호화 설정 (ISMS-P 컴플라이언스)
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 버킷 퍼블릭 액세스 차단 (보안 강화)
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 버킷 정책 - Terraform State 접근 제어
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnSecureCommunications"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "DenyInsecureConnections"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          NumericLessThan = {
            "s3:TlsVersion" = "1.2"
          }
        }
      },
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.terraform_state.arn
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/walb-terraform-state-trail"
          }
        }
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.terraform_state.arn}/cloudtrail-logs/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
            "AWS:SourceArn" = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/walb-terraform-state-trail"
          }
        }
      }
    ]
  })
}

# S3 버킷 라이프사이클 정책 (오래된 버전 정리)
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "terraform_state_lifecycle"
    status = "Enabled"

    # 이전 버전 관리
    noncurrent_version_expiration {
      noncurrent_days = 90  # 90일 후 이전 버전 삭제
    }

    # 삭제된 객체 표시 정리
    expiration {
      expired_object_delete_marker = true
    }

    # 불완전한 멀티파트 업로드 정리
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# =========================================
# DynamoDB Table for Terraform State Locking
# =========================================
resource "aws_dynamodb_table" "terraform_lock" {
  name           = local.table_name
  billing_mode   = "PAY_PER_REQUEST"  # 비용 효율적
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name        = local.table_name
    Description = "Terraform state 잠금용 DynamoDB 테이블"
  })

  # Point-in-time recovery 활성화 (보안 강화)
  point_in_time_recovery {
    enabled = true
  }

  # 서버 사이드 암호화 활성화
  server_side_encryption {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

# =========================================
# KMS Key for Enhanced Security (선택사항)
# =========================================
resource "aws_kms_key" "terraform_state" {
  description             = "WALB Terraform State 암호화용 KMS 키"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "walb-terraform-state-kms-key"
  })
}

resource "aws_kms_alias" "terraform_state" {
  name          = "alias/walb-terraform-state"
  target_key_id = aws_kms_key.terraform_state.key_id
}

# KMS 키 정책
resource "aws_kms_key_policy" "terraform_state" {
  key_id = aws_kms_key.terraform_state.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Terraform State Access"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "s3.${data.aws_region.current.name}.amazonaws.com"
          }
        }
      }
    ]
  })
}

# =========================================
# CloudWatch Log Group for Audit Trail
# =========================================
resource "aws_cloudwatch_log_group" "terraform_state_audit" {
  name              = "/aws/s3/terraform-state-audit"
  retention_in_days = 90

  tags = merge(local.common_tags, {
    Name = "terraform-state-audit-logs"
  })
}

# =========================================
# CloudTrail for State Bucket Monitoring (선택사항)
# =========================================
resource "aws_cloudtrail" "terraform_state" {
  count          = var.enable_cloudtrail_monitoring ? 1 : 0
  name           = "walb-terraform-state-trail"
  s3_bucket_name = aws_s3_bucket.terraform_state.bucket
  s3_key_prefix  = "cloudtrail-logs/"

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.terraform_state.arn}/*"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "walb-terraform-state-cloudtrail"
  })

  depends_on = [aws_s3_bucket_policy.terraform_state]
}