# =========================================
# Complete AWS Infrastructure Outputs
# =========================================

# =========================================
# VPC 및 네트워크 정보
# =========================================
output "vpc_info" {
  description = "VPC 관련 정보"
  value = {
    vpc_id               = module.vpc.vpc_id
    vpc_cidr             = module.vpc.vpc_cidr_block
    public_subnet_ids    = module.vpc.public_subnet_ids
    private_subnet_ids   = module.vpc.private_subnet_ids
    database_subnet_ids  = module.vpc.database_subnet_ids
    internet_gateway_id  = module.vpc.internet_gateway_id
    nat_gateway_ids      = module.vpc.nat_gateway_ids
    route_table_ids      = module.vpc.private_route_table_ids    # modules/vpc/outputs.tf 에 있는 route_table_id 들 중에 이건지 확실 x
  }
}

# =========================================
# EKS 클러스터 정보
# =========================================
output "eks_cluster_info" {
  description = "EKS 클러스터 정보"
  value = {
    cluster_id                    = module.eks.cluster_id
    cluster_name                  = module.eks.cluster_name
    cluster_arn                   = module.eks.cluster_arn
    cluster_endpoint              = module.eks.cluster_endpoint
    cluster_version               = module.eks.cluster_version
    cluster_security_group_id     = module.eks.cluster_security_group_id
    cluster_oidc_issuer_url       = module.eks.cluster_oidc_issuer_url
    oidc_provider_arn             = module.eks.oidc_provider_arn
    node_group_arn                = module.eks.eks_managed_node_groups.main.node_group_arn
    node_group_status             = module.eks.eks_managed_node_groups.main.node_group_status
    node_group_capacity_type      = var.enable_spot_instances ? "SPOT" : "ON_DEMAND"
    node_group_instance_types     = var.eks_node_instance_types
  }
  sensitive = true
}

# =========================================
# ALB 정보 (Ingress에서 자동 생성)
# =========================================
# ALB는 Kubernetes Ingress Controller가 자동으로 생성하므로
# Terraform에서 직접 관리하지 않음

# =========================================
# AWS Load Balancer Controller App2 정보
# =========================================
output "aws_load_balancer_controller_info" {
  description = "AWS Load Balancer Controller 정보"
  value = {
    service_account_name = "aws-load-balancer-controller"
    iam_role_arn        = try(module.load_balancer_controller_irsa_role[0].iam_role_arn, "")
    helm_release_name   = "aws-load-balancer-controller"
    namespace          = "kube-system"
  }
}

# EKS 접속을 위한 kubectl 명령어
output "eks_kubectl_config" {
  description = "kubectl 설정 명령어"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# =========================================
# RDS 데이터베이스 정보
# =========================================
output "rds_info" {
  description = "RDS 데이터베이스 정보"
  value = {
    db_instance_endpoint          = module.rds.db_instance_endpoint
    db_instance_arn              = module.rds.db_instance_arn
    db_instance_id               = module.rds.db_instance_id
    db_instance_port             = module.rds.db_instance_port
    engine                       = module.rds.engine_info.engine
    engine_version               = module.rds.engine_info.engine_version
    # engine_info = module.rds.engine_info
    db_subnet_group_name         = module.rds.db_subnet_group_name
    parameter_group_name         = module.rds.parameter_group_name
    security_group_id            = module.rds.security_group_id
  }
  sensitive = true
}

# RDS 연결 정보 (애플리케이션용)
output "rds_connection_info" {
  description = "애플리케이션에서 사용할 RDS 연결 정보"
  value = {
    host     = module.rds.db_instance_endpoint
    port     = module.rds.db_instance_port
    database = var.db_name
    username = var.db_username
  }
  sensitive = true
}

# =========================================
# S3 버킷 정보
# =========================================
output "s3_buckets_info" {
  description = "S3 버킷 정보"
  value = {
    logs_bucket_id         = module.s3.logs_bucket_id
    logs_bucket_arn          = module.s3.logs_bucket_arn
    logs_bucket_domain_name  = module.s3.logs_bucket_domain_name
    backups_bucket_domain_name         = module.s3.backups_bucket_domain_name
    backups_bucket_arn           = module.s3.backups_bucket_arn
    artifacts_bucket_domain_name     = module.s3.artifacts_bucket_domain_name
    artifacts_bucket_arn     = module.s3.artifacts_bucket_arn
  }
}

# =========================================
# DynamoDB 테이블 정보
# =========================================
output "dynamodb_tables_info" {
  description = "DynamoDB 테이블 정보"
  value = {
    security_logs_table = {
      name       = module.dynamodb_security_logs.table_name
      arn        = module.dynamodb_security_logs.table_arn
      id         = module.dynamodb_security_logs.table_id
      stream_arn = module.dynamodb_security_logs.table_stream_arn
    }
    user_sessions_table = {
      name       = module.dynamodb_user_sessions.table_name
      arn        = module.dynamodb_user_sessions.table_arn
      id         = module.dynamodb_user_sessions.table_id
      stream_arn = module.dynamodb_user_sessions.table_stream_arn
    }
  }
}

# 애플리케이션 환경 변수에서도 수정
output "application_environment_variables" {
  description = "EKS 애플리케이션에서 사용할 환경 변수"
  value = {
    # 데이터베이스 설정
    DB_HOST     = module.rds.db_instance_endpoint
    DB_PORT     = tostring(module.rds.db_instance_port)
    DB_NAME     = var.db_name
    DB_USER     = var.db_username
    
    # S3 설정
    S3_LOGGING_BUCKET     = module.s3.logs_bucket_id
    S3_BACKUP_BUCKET      = module.s3.backups_bucket_domain_name
    S3_APPLICATION_BUCKET = module.s3.artifacts_bucket_domain_name
    
    # DynamoDB 설정
    DYNAMODB_LOGS_TABLE     = module.dynamodb_security_logs.table_name
    DYNAMODB_SESSIONS_TABLE = module.dynamodb_user_sessions.table_name
    
    # AWS 설정
    AWS_REGION            = var.aws_region
    AWS_ACCOUNT_ID        = data.aws_caller_identity.current.account_id
    
    # KMS 키 정보
    KMS_KEY_ID            = aws_kms_key.main.key_id
  }
  sensitive = true
}

# =========================================
# 보안 설정 정보
# =========================================
output "security_configuration" {
  description = "보안 설정 정보"
  value = {
    kms_key_id               = aws_kms_key.main.key_id
    kms_key_arn             = aws_kms_key.main.arn
    kms_alias_name          = aws_kms_alias.main.name
    bastion_security_group_id = aws_security_group.bastion.id
    eks_app_role_arn        = aws_iam_role.eks_app_role.arn
    sns_topic_arn           = aws_sns_topic.security_alerts.arn
  }
}

# =========================================
# 모니터링 정보
# =========================================
output "monitoring_info" {
  description = "모니터링 관련 정보"
  value = {
    application_log_group_name = aws_cloudwatch_log_group.application_logs.name
    application_log_group_arn  = aws_cloudwatch_log_group.application_logs.arn
    security_log_group_name    = aws_cloudwatch_log_group.security_logs.name
    security_log_group_arn     = aws_cloudwatch_log_group.security_logs.arn
    sns_topic_arn             = aws_sns_topic.security_alerts.arn
  }
}

# =========================================
# 연결 문자열 및 엔드포인트
# =========================================
output "connection_strings" {
  description = "서비스 연결 문자열"
  value = {
    # PostgreSQL 연결 문자열
    postgres_connection = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_instance_endpoint}:${module.rds.db_instance_port}/${var.db_name}"
    
    # DynamoDB 엔드포인트
    dynamodb_endpoint = "https://dynamodb.${var.aws_region}.amazonaws.com"
    
    # S3 엔드포인트
    s3_endpoint = "https://s3.${var.aws_region}.amazonaws.com"
  }
  sensitive = true
}

# =========================================
# 배포 정보
# =========================================
output "deployment_info" {
  description = "배포 관련 정보"
  value = {
    terraform_version    = ">=1.0"
    aws_provider_version = "~>5.0"
    deployment_timestamp = timestamp()
    project_name         = var.project_name
    environment         = var.environment
    aws_region          = var.aws_region
    account_id          = data.aws_caller_identity.current.account_id
  }
}

# =========================================
# 비용 최적화 정보
# =========================================
output "cost_optimization_info" {
  description = "비용 최적화 관련 정보"
  value = {
    spot_instances_enabled = var.enable_spot_instances
    auto_scaling_enabled   = var.enable_auto_scaling
    multi_az_enabled      = var.enable_multi_az
    environment_tier      = var.environment
    estimated_monthly_cost = var.environment == "prod" ? "High" : var.environment == "staging" ? "Medium" : "Low"
  }
}

# =========================================
# 보안 체크리스트
# =========================================
output "security_checklist" {
  description = "보안 설정 체크리스트"
  value = {
    encryption_at_rest_enabled    = var.enable_encryption_at_rest
    encryption_in_transit_enabled = var.enable_encryption_in_transit
    vpc_flow_logs_enabled        = var.enable_vpc_flow_logs
    cloudtrail_enabled           = var.enable_cloudtrail
    guardduty_enabled            = var.enable_guardduty
    security_hub_enabled         = var.enable_security_hub
    config_enabled               = var.enable_config
    kms_key_rotation_enabled     = true
    multi_az_enabled             = var.enable_multi_az
    backup_enabled               = true
    monitoring_enabled           = var.enable_detailed_monitoring
  }
}

# =========================================
# IAM Security 정보
# =========================================
output "iam_security_info" {
  description = "IAM Security 모듈에서 생성된 리소스 정보"
  value = {
    # Users
    blog_s3_user_name     = module.iam_security.blog_s3_user_name
    blog_s3_user_arn      = module.iam_security.blog_s3_user_arn
    splunk_kinesis_reader_name = module.iam_security.splunk_kinesis_reader_name
    splunk_kinesis_reader_arn  = module.iam_security.splunk_kinesis_reader_arn
    
    # Roles
    cloudtrail_cloudwatch_role_name = module.iam_security.cloudtrail_cloudwatch_role_name
    cloudtrail_cloudwatch_role_arn  = module.iam_security.cloudtrail_cloudwatch_role_arn
    cloudwatch_kinesis_role_name    = module.iam_security.cloudwatch_kinesis_role_name
    cloudwatch_kinesis_role_arn     = module.iam_security.cloudwatch_kinesis_role_arn
    firehose_role_name              = module.iam_security.firehose_role_name
    firehose_role_arn               = module.iam_security.firehose_role_arn
    
    # Policies
    blog_s3_policy_arn              = module.iam_security.blog_s3_policy_arn
    splunk_kinesis_policy_arn       = module.iam_security.splunk_kinesis_policy_arn
    cloudtrail_cloudwatch_policy_arn = module.iam_security.cloudtrail_cloudwatch_policy_arn
    cloudwatch_kinesis_policy_arn   = module.iam_security.cloudwatch_kinesis_policy_arn
    firehose_waf_policy_arn         = module.iam_security.firehose_waf_policy_arn
  }
}

# =========================================
# IAM Security Credentials (sensitive)
# =========================================
output "iam_security_credentials" {
  description = "IAM Security 사용자 자격 증명 (민감 정보)"
  value = {
    blog_s3_user_access_key_id        = module.iam_security.blog_s3_user_access_key_id
    splunk_kinesis_reader_access_key_id = module.iam_security.splunk_kinesis_reader_access_key_id
    blog_s3_credentials_secret_arn      = module.iam_security.blog_s3_credentials_secret_arn
    splunk_kinesis_credentials_secret_arn = module.iam_security.splunk_kinesis_credentials_secret_arn
  }
  sensitive = true
}

# =========================================
# 트러블슈팅 정보
# =========================================
output "troubleshooting_info" {
  description = "트러블슈팅을 위한 정보"
  value = {
    vpc_id                   = module.vpc.vpc_id
    private_subnet_ids       = module.vpc.private_subnet_ids
    security_group_ids = {
      eks_cluster = module.eks.cluster_security_group_id
      rds         = module.rds.security_group_id
      bastion     = aws_security_group.bastion.id
    }
    iam_roles = {
      eks_app_role = aws_iam_role.eks_app_role.arn
    }
    log_groups = {
      application = aws_cloudwatch_log_group.application_logs.name
      security    = aws_cloudwatch_log_group.security_logs.name
    }
  }
}

# =========================================
# ALB 서브넷 설정 (Ingress용)
# =========================================
output "alb_subnet_config" {
  description = "ALB Ingress에서 사용할 서브넷 설정"
  value = {
    # 서로 다른 AZ의 퍼블릭 서브넷 2개 선택
    public_subnets_for_alb = join(",", slice(module.vpc.public_subnet_ids, 0, 2))
    all_public_subnets     = module.vpc.public_subnet_ids
  }
}

# =========================================
# 다음 단계 안내
# =========================================
output "next_steps" {
  description = "배포 후 다음 단계"
  value = {
    kubectl_config = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
    verify_cluster = "kubectl get nodes"
    check_pods     = "kubectl get pods --all-namespaces"
    access_rds     = "Use the RDS endpoint: ${module.rds.db_instance_endpoint}"
    view_logs      = "Check CloudWatch logs in: ${aws_cloudwatch_log_group.application_logs.name}"
    alb_subnets    = "Use these subnets for ALB: ${join(",", slice(module.vpc.public_subnet_ids, 0, 2))}"
  }
}

# =========================================
# GitHub Actions OIDC 정보
# =========================================
output "github_actions_roles" {
  description = "GitHub Actions에서 사용할 IAM 역할 정보"
  value = {
    infrastructure_role_arn = aws_iam_role.github_actions_infra.arn
    application_role_arn   = aws_iam_role.github_actions_app.arn
    oidc_provider_arn      = aws_iam_openid_connect_provider.github_actions.arn
  }
}

output "github_secrets_setup" {
  description = "GitHub Secrets에 설정할 값들"
  value = {
    AWS_ROLE_ARN_INFRA = aws_iam_role.github_actions_infra.arn
    AWS_ROLE_ARN_APP   = aws_iam_role.github_actions_app.arn
    AWS_REGION         = var.aws_region
    AWS_ACCOUNT_ID     = data.aws_caller_identity.current.account_id
    DB_PASSWORD        = var.db_password
  }
  sensitive = true
}

output "rds_endpoint" {
  description = "RDS 엔드포인트"
  value       = module.rds.db_instance_endpoint
}

output "db_name" {
  description = "데이터베이스 이름"
  value       = var.db_name
}

output "db_username" {
  description = "데이터베이스 사용자명"
  value       = var.db_username
}

output "db_port" {
  description = "데이터베이스 포트"
  value       = module.rds.db_instance_port
}

# =========================================
# Bastion Host 정보
# =========================================
output "bastion_public_ip" {
  description = "Bastion Host 공인 IP"
  value       = var.enable_bastion_host ? aws_instance.bastion[0].public_ip : null
}

output "bastion_private_ip" {
  description = "Bastion Host 사설 IP"
  value       = var.enable_bastion_host ? aws_instance.bastion[0].private_ip : null
}