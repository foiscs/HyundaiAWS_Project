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
    bucket         = "walb-terraform-state-6026"  # bootstrap에서 생성된 버킷명
    key            = "infrastructure/walb_terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "walb-terraform-lock-6026"   # bootstrap에서 생성된 테이블명
    kms_key_id     = "arn:aws:kms:ap-northeast-2:902597156026:key/bc9a4347-e66d-4127-b605-549944cdc942"            # bootstrap에서 생성된 KMS 키
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

# =========================================
# Kubernetes Provider
# =========================================
provider "kubernetes" {
  host                   = try(module.eks.cluster_endpoint, "")
  cluster_ca_certificate = try(base64decode(module.eks.cluster_certificate_authority_data), "")
  
  dynamic "exec" {
    for_each = can(module.eks.cluster_name) ? [1] : []
    content {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        module.eks.cluster_name,
        "--region",
        var.aws_region
      ]
    }
  }
}

# =========================================
# Helm Provider
# =========================================
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        module.eks.cluster_name,
        "--region",
        var.aws_region
      ]
    }
  }
}

