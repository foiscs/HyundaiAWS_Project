# =========================================
# Terraform Providers Configuration
# =========================================

terraform {
  required_version = ">= 1.8"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70.0"
    }
    
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1"
    }
    
    local = {
      source  = "hashicorp/local"
      version = "~> 2.1"
    }
  }
  backend "s3" {
    bucket         = "walb-terraform-state-3163"  # bootstrap에서 생성된 버킷명
    key            = "infrastructure/terraform2.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "walb-terraform-lock-3163"   # bootstrap에서 생성된 테이블명
    kms_key_id     = "arn:aws:kms:ap-northeast-2:253157413163:key/4c10b1b0-e7df-4ace-a79c-37763dd29fc3"            # bootstrap에서 생성된 KMS 키
  }
}

# =========================================
# AWS Provider
# =========================================
provider "aws" {
  region = var.aws_region

  # 기본 태그 설정
  default_tags {
    tags = {
      Project       = var.project_name
      Environment   = var.environment
      ManagedBy     = "Terraform"
      Owner         = var.owner
      CostCenter    = var.cost_center
      #CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
      #TerraformPath = path.cwd
    }
  }

  # AssumeRole 설정 (교차 계정 접근 시 사용)
  # assume_role {
  #   role_arn = "arn:aws:iam::ACCOUNT-ID:role/TerraformRole"
  # }
}

# EKS 클러스터와 통신하기 위한 인증 토큰을 가져온다.
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

# =========================================
# Kubernetes Provider
# =========================================
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  token                  = data.aws_eks_cluster_auth.this.token
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
}

# =========================================
# Helm Provider
# =========================================
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    token                  = data.aws_eks_cluster_auth.this.token
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  }
}
