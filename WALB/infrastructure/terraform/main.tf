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

# =========================================
# EKS Module - Kubernetes 클러스터
# =========================================
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
  table_name   = "security-logs-metadata"
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
  table_name   = "user-sessions"
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
    module.eks.cluster_security_group_id
  ]
  
  # 데이터베이스 설정
  engine                 = "postgres"
  engine_version         = "16.4"
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
  enabled_cloudwatch_logs_exports = ["postgresql"]
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

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
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
          "rds:DescribeDBClusters"
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
# Application Load Balancer
# =========================================
resource "aws_lb" "main" {
  count              = var.enable_load_balancer ? 1 : 0
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = var.lb_type
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = module.vpc.public_subnet_ids

  enable_deletion_protection = false

  tags = merge(local.common_tags, {
    Name        = "${var.project_name}-alb"
    Component   = "LoadBalancer"
  })
}

resource "aws_security_group" "alb" {
  count       = var.enable_load_balancer ? 1 : 0
  name_prefix = "${var.project_name}-alb"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Application Load Balancer"

  # HTTP 접근 허용
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS 접근 허용
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 모든 outbound 트래픽 허용
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-alb-sg"
    Component = "LoadBalancer"
  })
}

# ALB Target Group
resource "aws_lb_target_group" "eks_nodes" {
  count       = var.enable_load_balancer ? 1 : 0
  name        = "${var.project_name}-eks-nodes-tg"
  port        = var.application_port
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  tags = merge(local.common_tags, {
    Name                                        = "${var.project_name}-eks-nodes-tg"
    Component                                   = "LoadBalancer"
    "kubernetes.io/service-name"               = "default/example-service"
    "kubernetes.io/cluster/${local.cluster_name}" = "owned"
  })
}

# ALB Listener
resource "aws_lb_listener" "eks_nodes" {
  count             = var.enable_load_balancer ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.eks_nodes[0].arn
  }

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-alb-listener"
    Component = "LoadBalancer"
  })
}

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

  name = "myapp"
  tags = {
    Environment = "dev"
    Project     = "myproject"
  }
}

