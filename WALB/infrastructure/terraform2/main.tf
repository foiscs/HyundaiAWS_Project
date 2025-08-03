# =========================================
# Complete AWS Infrastructure Configuration
# =========================================

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# =========================================
# VPC Module - 네트워크 기반 구성
# =========================================
module "vpc" {
  source = "./modules/vpc"

  project_name        = var.project_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnets
  private_subnet_cidrs = var.private_subnets
  database_subnet_cidrs = var.database_subnets

  enable_nat_gateway     = true
  enable_dns_hostnames   = true
  enable_dns_support     = true
  enable_vpc_flow_logs   = var.enable_vpc_flow_logs

  common_tags = merge(local.common_tags, {
    Component = "Networking"
  })
}

# =========================================
# S3 Module - 스토리지 및 로깅
# =========================================
module "s3" {
  source = "./modules/s3"

  project_name = var.project_name

  # 로깅용 S3 버킷들
  create_backups_bucket     = true
  create_artifacts_bucket   = true

  # 보안 설정
  enable_versioning           = true
  enable_mfa_delete          = false

  # 라이프사이클 관련 변수
  transition_to_ia_days           = 30
  transition_to_glacier_days      = 90
  transition_to_deep_archive_days = 180
  log_retention_days              = 365
  backup_retention_days           = 2555

  common_tags = merge(local.common_tags, {
    Component = "Storage"
  })
}

# =========================================
# KMS Key for Encryption (중앙 집중식)
# =========================================
resource "aws_kms_key" "main" {
  description             = "KMS key for ${var.project_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

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
        Sid    = "Allow EKS Service"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-kms"
    Component = "Security"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.project_name}-test"
  target_key_id = aws_kms_key.main.key_id
}

# EKS Module - Kubernetes 클러스터
module "eks" {
  source = "./modules/eks"

  project_name = var.project_name

  # 클러스터 설정
  cluster_name    = local.cluster_name
  cluster_version = "1.32"

  # 네트워크 설정
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  subnet_ids         = module.vpc.private_subnet_ids

  # 보안 설정
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

  # 로깅 설정
  cluster_enabled_log_types = [
    "api",
    "audit", 
    "authenticator",
    "controllerManager",
    "scheduler"
  ]
  log_retention_days = var.security_log_retention_days

  # IRSA 설정
  enable_irsa = true

  enable_load_balancer = var.enable_load_balancer
  
  # 애드온 설정
  enable_vpc_cni_addon    = true
  enable_coredns_addon    = true
  enable_kube_proxy_addon = true
  
  # 노드 그룹 설정
  node_group_name = "${var.project_name}-nodes"
  eks_node_instance_types = var.eks_node_instance_types
  capacity_type = var.enable_spot_instances ? "SPOT" : "ON_DEMAND"
  
  # 스케일링 설정
  eks_node_desired_capacity = var.eks_node_desired_capacity
  eks_node_max_capacity     = var.eks_node_max_capacity
  eks_node_min_capacity     = var.eks_node_min_capacity
  
  # 보안 설정
  enable_ssh_access = var.enable_bastion_host
  ec2_key_pair_name = var.ec2_key_pair_name
  
  # 시작 템플릿 설정
  create_launch_template = true
  ebs_volume_type = "gp3"
  ebs_volume_size = 30

  common_tags = merge(local.common_tags, {
    Component = "Compute"
  })

  depends_on = [module.vpc, aws_kms_key.main]
}



# =========================================
# DynamoDB Module - NoSQL 데이터베이스
# =========================================

# 보안 로그 메타데이터 테이블
module "dynamodb_security_logs" {
  source = "./modules/dynamodb"

  project_name = var.project_name

  # 테이블 기본 설정
  table_name   = "walb2-security-logs-metadata"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "log_id"
  range_key    = "timestamp"
  
  # 속성 정의
  attributes = [
    {
      name = "log_id"
      type = "S"
    },
    {
      name = "timestamp"
      type = "S"
    },
    {
      name = "source_service"
      type = "S"
    }
  ]

  # 글로벌 보조 인덱스
  global_secondary_indexes = [
    {
      name               = "source-service-index"
      hash_key           = "source_service"
      range_key          = "timestamp"
      projection_type    = "ALL"
      read_capacity      = null
      write_capacity     = null
      non_key_attributes = []
    }
  ]

  # 보안 및 백업 설정
  point_in_time_recovery_enabled = true
  stream_enabled                 = true
  stream_view_type              = "NEW_AND_OLD_IMAGES"
  ttl_enabled                   = true
  ttl_attribute_name            = "expiry_time"
  
  # 암호화 설정
  create_kms_key = true
  
  # 태그
  common_tags = merge(local.common_tags, {
    Component = "Database"
    DataType  = "SecurityLogs"
  })
}

# 사용자 세션 테이블
module "dynamodb_user_sessions" {
  source = "./modules/dynamodb"

  project_name = var.project_name

  # 테이블 기본 설정
  table_name   = "walb2-user-sessions"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "session_id"
  range_key    = null
  
  # 속성 정의
  attributes = [
    {
      name = "session_id"
      type = "S"
    },
    {
      name = "user_id"
      type = "S"
    }
  ]

  # 글로벌 보조 인덱스
  global_secondary_indexes = [
    {
      name               = "user-id-index"
      hash_key           = "user_id"
      range_key          = null
      projection_type    = "ALL"
      read_capacity      = null
      write_capacity     = null
      non_key_attributes = []
    }
  ]

  # 보안 및 백업 설정
  point_in_time_recovery_enabled = true
  stream_enabled                 = false
  ttl_enabled                   = true
  ttl_attribute_name            = "expires_at"
  
  # 암호화 설정
  create_kms_key = true
  
  # 태그
  common_tags = merge(local.common_tags, {
    Component = "Database"
    DataType  = "UserSessions"
  })
}

# =========================================
# RDS Module - 관계형 데이터베이스
# =========================================
module "rds" {
  source = "./modules/rds"

  project_name = var.project_name

  # 네트워크 설정
  vpc_id                = module.vpc.vpc_id
  database_subnet_ids   = module.vpc.database_subnet_ids
 
  allowed_security_groups = [
    module.eks.cluster_security_group_id,
    module.eks.node_security_group_id,
    aws_security_group.bastion.id
  ]
  
  # 데이터베이스 설정
  engine                 = "mysql"
  engine_version         = "8.0.39"
  instance_class         = var.rds_instance_class
  allocated_storage      = 20
  max_allocated_storage  = 100

  # 인증 설정
  database_name     = var.db_name
  master_username   = var.db_username
  master_password   = var.db_password

  # 백업 설정
  backup_retention_period = var.backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # 모니터링 설정
  monitoring_interval = 60
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  log_retention_days = var.security_log_retention_days

  # Multi-AZ 설정
  multi_az = var.enable_multi_az

  # 보안 설정
  deletion_protection = false
  
  common_tags = merge(local.common_tags, {
    Component = "Database"
  })

  depends_on = [module.vpc]
}

# =========================================
# SNS Topic for Security Alerts
# =========================================
resource "aws_sns_topic" "security_alerts" {
  name = "${var.project_name}-security-alerts"

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-security-alerts"
    Component = "Notifications"
  })
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count     = length(var.alert_email_addresses)
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# =========================================
# CloudWatch Log Groups (중앙 집중식)
# =========================================
resource "aws_cloudwatch_log_group" "application_logs" {
  name              = "/aws/application/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-app-logs"
    Component = "Monitoring"
  })
}

resource "aws_cloudwatch_log_group" "security_logs" {
  name              = "/aws/security/${var.project_name}"
  retention_in_days = var.security_log_retention_days

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-security-logs"
    Component = "Monitoring"
  })
}

# =========================================
# Bastion Host Security Group (EKS 접근용)
# =========================================
resource "aws_security_group" "bastion" {
  name_prefix = "${var.project_name}-bastion"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for bastion host access"

  # 기존 SSH 접근 (VPC 내부)
  ingress {
    description = "SSH from VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  # GitHub Actions를 위한 전체 인터넷 SSH 접근 (임시 또는 조건부)
  ingress {
    description = "SSH from GitHub Actions"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # 보안상 위험하지만 GitHub Actions용
  }


  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-bastion-sg"
    Component = "Security"
  })
}

# =========================================
# IAM Role for EKS Applications
# =========================================
resource "aws_iam_role" "eks_app_role" {
  name = "${var.project_name}-eks-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${module.eks.cluster_oidc_issuer_url}:sub" = "system:serviceaccount:default:eks-app-service-account"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-eks-app-role"
    Component = "Security"
  })
}

# terraform import kubernetes_config_map.aws_auth kube-system/aws-auth 필요

# =========================================
# aws-auth ConfigMap for GitHub Actions Access
# =========================================
resource "kubernetes_config_map" "aws_auth" {
  depends_on = [module.eks]
  
  metadata {
    name      = "aws-auth"
    namespace = "kube-system"
  }

  data = {
    mapRoles = yamlencode([
      # EKS 노드 그룹 역할
      {
        rolearn  = module.eks.eks_managed_node_groups.main.iam_role_arn
        username = "system:node:{{EC2PrivateDNSName}}"
        groups   = ["system:bootstrappers", "system:nodes"]
      },
      # 현재 사용자를 관리자로 추가
      {
        rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        username = "cluster-creator"
        groups   = ["system:masters"]
      },
      # GitHub Actions 애플리케이션 배포 역할
      {
        rolearn  = aws_iam_role.github_actions_app.arn
        username = "github-actions-app"
        groups   = ["system:masters"]
      },
      # GitHub Actions 인프라 배포 역할
      {
        rolearn  = aws_iam_role.github_actions_infra.arn
        username = "github-actions-infra"
        groups   = ["system:masters"]
      },
    ])
    
    mapUsers = yamlencode([
      # 현재 사용자를 직접 매핑
      {
        userarn  = data.aws_caller_identity.current.arn
        username = "admin"
        groups   = ["system:masters"]
      }
    ])
  }
}

# EKS 애플리케이션용 정책 연결
resource "aws_iam_role_policy" "eks_app_policy" {
  name = "eks-app-policy"
  role = aws_iam_role.eks_app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.s3.logs_bucket_arn,
          "${module.s3.logs_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.dynamodb_security_logs.table_arn,
          module.dynamodb_user_sessions.table_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          aws_cloudwatch_log_group.application_logs.arn,
          aws_cloudwatch_log_group.security_logs.arn,
          "${aws_cloudwatch_log_group.application_logs.arn}:*",
          "${aws_cloudwatch_log_group.security_logs.arn}:*"
        ]
      }
    ]
  })
}

# =========================================
# ALB는 Kubernetes Ingress에서 자동 생성됨
# AWS Load Balancer Controller가 관리
# =========================================

# =========================================
# Local Values (공통 설정)
# =========================================
locals {
  cluster_name = var.cluster_name != "" ? var.cluster_name : "${var.project_name}-eks"
  
  common_tags = merge(var.additional_tags, {
    Terraform   = "true"
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "Terraform"
    CostCenter  = var.cost_center
  })
}


module "ecr" {
  source = "./modules/ecr"

  name = "${var.project_name}-ecr"
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# =========================================
# GitHub Actions OIDC Provider and IAM Role
# =========================================

# GitHub OIDC Identity Provider
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = merge(local.common_tags, {
    Name      = "walb2-app-github-oidc-provider"
    Component = "CI/CD"
  })

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [thumbprint_list]
    prevent_destroy       = false
  }
}


# GitHub Actions IAM Role for Infrastructure (Terraform)
resource "aws_iam_role" "github_actions_infra" {
  name = "${var.project_name}-github-actions-infra-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-github-actions-infra-role"
    Component = "CI/CD"
    Purpose   = "Infrastructure"
  })
}

# GitHub Actions IAM Role for Application Deployment
resource "aws_iam_role" "github_actions_app" {
  name = "${var.project_name}-github-actions-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-github-actions-app-role"
    Component = "CI/CD"
    Purpose   = "Application"
  })
}

# Infrastructure 배포용 정책 (Terraform 권한)
resource "aws_iam_role_policy" "github_actions_infra_policy" {
  name = "github-actions-infra-policy"
  role = aws_iam_role.github_actions_infra.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # Terraform State 관리
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketVersioning",
          "s3:CreateBucket",
          "s3:PutBucketVersioning",
          "s3:PutBucketEncryption",
          "s3:PutBucketPublicAccessBlock",
          
          # DynamoDB State Locking
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:CreateTable",
          "dynamodb:DescribeTable",
          
          # 모든 인프라 리소스 관리
          "ec2:*",
          "vpc:*",
          "rds:*",
          "eks:*",
          "s3:*",
          "dynamodb:*",
          "iam:*",
          "kms:*",
          "logs:*",
          "cloudtrail:*",
          "sns:*",
          "elasticloadbalancing:*",
          "ecr:*",
          "ssm:*",
          "cloudwatch:*",
          
          # 리소스 조회 권한
          "tag:GetResources",
          "tag:TagResources",
          "tag:UntagResources",
          "resource-groups:*",
          
          # 계정 정보 조회
          "sts:GetCallerIdentity",
          "sts:AssumeRole"
        ]
        Resource = "*"
      }
    ]
  })
}

# Application 배포용 정책 (ECR, EKS, RDS 접근)
resource "aws_iam_role_policy" "github_actions_app_policy" {
  name = "github-actions-app-policy"
  role = aws_iam_role.github_actions_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # ECR 권한
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeRepositories",
          "ecr:DescribeImages",
          
          # EKS 권한
          "eks:DescribeCluster",
          "eks:DescribeNodegroup",
          "eks:ListClusters",
          "eks:AccessKubernetesApi",
          
          # RDS 권한 (스키마 적용용)
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:ListTagsForResource",
          
          # S3 권한 (애플리케이션 파일 업로드용)
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          
          # CloudWatch 로그
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          
          # LoadBalancer 조회
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeTargetGroups",

          # SSM Parameter Store 권한
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
          
          # EC2 권한 추가 (Bastion Host 및 네트워크 조회용)
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:DescribeTags",
          "ec2:DescribeSubnets",
          "ec2:DescribeRouteTables",
          "ec2:DescribeVpcs",
          
          # 보안그룹 권한 추가 (kubelet 통신 규칙 확인/수정용)
          "ec2:DescribeSecurityGroups",
          "ec2:AuthorizeSecurityGroupIngress",
          
          # 계정 정보 조회
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      }
    ]
  })
}

# =========================================
# EC2 Key Pair for Bastion Host
# =========================================
resource "tls_private_key" "bastion_key" {
  count     = var.enable_bastion_host ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "bastion_key" {
  count      = var.enable_bastion_host ? 1 : 0
  key_name   = "${var.project_name}-bastion-key"
  public_key = tls_private_key.bastion_key[0].public_key_openssh

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-bastion-key"
    Component = "Bastion"
  })
}

# SSH 개인키를 SSM Parameter Store에 저장
resource "aws_ssm_parameter" "bastion_private_key" {
  count = var.enable_bastion_host ? 1 : 0
  name  = "/${var.project_name}/bastion/ssh-private-key"
  type  = "SecureString"
  value = tls_private_key.bastion_key[0].private_key_pem

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-bastion-ssh-key"
  })
}

# 기존 DB 비밀번호를 Parameter Store에 저장 (참조용)
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/rds/master-password"
  type  = "SecureString"
  value = var.db_password  # 기존에 정의된 변수 사용

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-db-password"
  })
}

# =========================================
# Bastion Host EC2 Instance
# =========================================
resource "aws_instance" "bastion" {
  count                  = var.enable_bastion_host ? 1 : 0
  ami                   = data.aws_ami.amazon_linux.id
  instance_type         = var.bastion_instance_type
  key_name              = aws_key_pair.bastion_key[0].key_name
  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id             = module.vpc.public_subnet_ids[0]
  
  # MySQL 클라이언트 및 네트워크 도구 설치를 위한 user data
  user_data = base64encode(<<-EOF
    #!/bin/bash
    yum update -y
    
    # MySQL 클라이언트 설치
    yum install -y mysql
    
    # 네트워크 진단 도구 설치
    yum install -y telnet nc nmap-ncat
    
    # AWS CLI 설치 (최신 버전)
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    
    # kubectl 설치
    curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.28.3/2023-11-14/bin/linux/amd64/kubectl
    chmod +x ./kubectl
    mv ./kubectl /usr/local/bin
    
    echo "Bastion host setup completed" > /var/log/bastion-setup.log
  EOF
  )

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-bastion-host"
    Component = "Bastion"
  })
}

# AMI 데이터 소스
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# # IAM Security Module  
# module "iam_security" {                             
#   source = "./modules/iam-security"                 
#   project_name        = var.project_name            
#   s3_logs_bucket_name = module.s3.logs_bucket_name  
#   #s3_logs_bucket_name = "walb2-app-logs-walb-87d08755"
#   create_access_keys  = true  # 보안상 기본값 false
#   common_tags = merge(local.common_tags, {          
#     Component = "Security"                          
#     Purpose   = "User Management"                   
#   })
#   depends_on = [module.s3]
# }

# # CloudTrail Hub Module
# module "cloudtrail" {
#   source = "./modules/cloudtrail"
#   project_name                    = var.project_name
#   s3_bucket_name                  = module.s3.logs_bucket_name
#   cloudtrail_cloudwatch_role_arn  = module.iam_security.cloudtrail_cloudwatch_role_arn
#   cloudwatch_kinesis_role_arn     = module.iam_security.cloudwatch_kinesis_role_arn
#   kms_key_arn                     = aws_kms_key.main.arn
#   sns_topic_arn                   = aws_sns_topic.security_alerts.arn
  

#   common_tags = merge(local.common_tags, {
#     Component = "Security"
#   })
  
#   depends_on = [module.iam_security, module.s3]
# }

# # # Security Hub Module
# module "security_hub" {
#   source = "./modules/securityhub"
  
#   project_name                = var.project_name
#   cloudwatch_kinesis_role_arn = module.iam_security.cloudwatch_kinesis_role_arn
#   kms_key_arn                 = aws_kms_key.main.arn
#   sns_topic_arn               = aws_sns_topic.security_alerts.arn
  
#   # Security Hub 설정
#   enable_default_standards = true
#   enable_aws_foundational  = true
#   enable_cis_standard      = true
  
#   # Kinesis 설정
#   kinesis_shard_count     = 1
#   kinesis_retention_hours = 24

#   # 모니터링 설정
#   enable_monitoring        = true

#   # 로그 설정
#   log_retention_days = var.security_log_retention_days
#   log_filter_pattern = ""

#     common_tags = merge(local.common_tags, {
#     Component = "Security"
#     Service   = "SecurityHub"
#   })

#   depends_on = [module.iam_security]
# }

# # GuardDuty Module
# module "guardduty" {
#   source = "./modules/guardduty"
#   project_name                = var.project_name
#   cloudwatch_kinesis_role_arn = module.iam_security.cloudwatch_kinesis_role_arn
#   kms_key_arn                 = aws_kms_key.main.arn
#   sns_topic_arn               = aws_sns_topic.security_alerts.arn        
#   # GuardDuty 설정
#   finding_publishing_frequency = "FIFTEEN_MINUTES"
#   enable_s3_protection        = true
#   enable_kubernetes_protection = true
#   enable_malware_protection   = true
  
#   # Kinesis 설정
#   kinesis_shard_count     = 1
#   kinesis_retention_hours = 24
  
#   # 모니터링 설정
#   enable_monitoring        = true
#   high_severity_threshold  = 3
#   # 로그 설정
#   log_retention_days = var.security_log_retention_days
#   log_filter_pattern = ""
  
#   common_tags = merge(local.common_tags, {
#     Component = "Security"
#     Service   = "GuardDuty"
#   })
  
#   depends_on = [module.iam_security]
# }

# # WAF Module
# module "waf" {
#   source = "./modules/waf"
#   project_name     = var.project_name
#   target_alb_name  = "walb2-app-ingress-alb"  # EKS Ingress에서 생성되는 ALB 이름
#   # WAF 설정
#   rate_limit             = 2000
#   blocked_ip_addresses   = []  # 필요시 차단할 IP 추가
#   blocked_requests_threshold = 100
  
#   # Firehose 설정
#   firehose_role_arn       = module.iam_security.firehose_role_arn  # IAM Security 모듈에서 생성 필요
#   s3_bucket_arn           = module.s3.logs_bucket_arn
#   buffer_size_mb          = 5
#   buffer_interval_seconds = 300
#   # 모니터링 설정
#   enable_monitoring = true
#   kms_key_arn      = aws_kms_key.main.arn
#   # 로그 설정
#   log_retention_days = var.security_log_retention_days
  
#   # 데이터 변환 설정 (선택적)
#   enable_data_transformation = false
#   lambda_processor_arn       = null
  
#   common_tags = merge(local.common_tags, {
#     Component = "Security"
#     Service   = "WAF"
#   })
  
#   depends_on = [module.eks, module.iam_security, module.s3]
# }

# # =========================================
# # VPC Flow Logs Module
# # =========================================
# module "vpcflow" {
#   source = "./modules/vpcflow"
#   project_name = var.project_name
#   vpc_id       = module.vpc.vpc_id
#   # S3 설정
#   vpc_flow_logs_s3_arn = "${module.s3.logs_bucket_arn}/vpc-flow-logs/"
#   s3_bucket_name       = module.s3.logs_bucket_name
#   # Flow Logs 설정
#   traffic_type = "ALL"
#   vpc_flow_logs_format = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${windowstart} $${windowend} $${action} $${flowlogstatus} $${vpc-id} $${subnet-id} $${instance-id} $${tcp-flags} $${type} $${pkt-srcaddr} $${pkt-dstaddr} $${region} $${az-id}"
#   # S3 파티셔닝 옵션
#   enable_hive_partitions   = true
#   enable_hourly_partitions = true
#   # S3 라이프사이클 설정
#   enable_s3_lifecycle              = true
#   transition_to_ia_days           = 30
#   transition_to_glacier_days      = 90
#   transition_to_deep_archive_days = 365
#   vpc_flow_logs_retention_days    = 2555  # 7 years
#   common_tags = merge(local.common_tags, {
#     Component = "Security"
#     Service   = "VPCFlowLogs"
#   })
#   depends_on = [module.vpc, module.s3]
# }

# # DNS Resolve Logging Module
# module "dnsresolve" {
#   source = "./modules/dnsresolve"
#   project_name         = var.project_name
#   environment         = var.environment
#   common_tags         = local.common_tags
#   # Route 53 Configuration
#   hosted_zone_id      = var.hosted_zone_id
#   # S3 Configuration
#   s3_logs_bucket_name = module.s3.logs_bucket_name

#   vpc_id                  = module.vpc.vpc_id
  
#   # S3 Lifecycle Configuration
#   enable_s3_lifecycle             = var.enable_s3_lifecycle
#   transition_to_ia_days          = var.transition_to_ia_days
#   transition_to_glacier_days     = var.transition_to_glacier_days
#   transition_to_deep_archive_days = var.transition_to_deep_archive_days
#   dns_log_retention_days         = var.dns_log_retention_days
  
#   depends_on = [
#     module.s3,
#     module.vpc
#   ]
# }