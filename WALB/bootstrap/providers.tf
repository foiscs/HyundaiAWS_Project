# =========================================
# Bootstrap Terraform Configuration
# =========================================
# Backend 리소스 생성용 Terraform 설정
# 이 파일은 로컬 state를 사용하여 S3 backend 리소스들을 생성

terraform {
  required_version = ">= 1.0"
  
  # 로컬 state 사용 (backend 리소스 생성이므로)
  # backend 설정 없음 - terraform.tfstate 파일이 로컬에 생성됨
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.29.0"
    }
    
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# =========================================
# AWS Provider Configuration
# =========================================
provider "aws" {
  region = var.aws_region

  # 기본 태그 설정 (모든 리소스에 자동 적용)
  default_tags {
    tags = {
      Project       = "WALB"
      Environment   = "bootstrap"
      Purpose       = "TerraformBackend"
      ManagedBy     = "Terraform"
      Owner         = "DevSecOps Team"
      CostCenter    = "Infrastructure"
      CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
      Component     = "Bootstrap"
    }
  }
}

# =========================================
# Random Provider Configuration
# =========================================
provider "random" {
  # random provider는 특별한 설정이 필요하지 않음
}