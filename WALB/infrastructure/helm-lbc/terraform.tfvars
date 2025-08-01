# AWS Load Balancer Controller Helm 배포를 위한 변수 값
# 자동 생성됨: #오후

# 기본 정보 (terraform output에서 자동 수집)
project_name = "walb-app"
environment  = "dev"
aws_region   = "ap-northeast-2"

# EKS 클러스터 정보 (terraform output에서 자동 수집)
cluster_name = "walb-eks-cluster"
vpc_id       = "vpc-0d260122fbe607489"

# AWS Load Balancer Controller 설정
service_account_name = "aws-load-balancer-controller"
namespace           = "kube-system"
chart_version       = "1.8.1"
replica_count       = 2

# 이미지 설정
image_repository = "602401143452.dkr.ecr.ap-northeast-2.amazonaws.com/amazon/aws-load-balancer-controller"

# 기능 설정
enable_shield = false
enable_waf    = false
enable_wafv2  = false

# 로깅 설정
log_level = "info"

# 웹훅 설정
webhook_timeout_seconds = 30
webhook_failure_policy  = "Ignore"

# 리소스 설정
resource_limits_cpu      = "1000m"
resource_limits_memory   = "2Gi"
resource_requests_cpu    = "500m"
resource_requests_memory = "1Gi"

# 추가 태그
additional_tags = {
  Owner      = "DevOps-Team"
  CostCenter = "Engineering"
  CreatedBy  = "AutoScript"
  Timestamp  = "2025-08-01T17:11:00Z"
}
