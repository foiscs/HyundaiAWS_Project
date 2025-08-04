#!/bin/bash

# AWS Load Balancer Controller Helm 배포를 위한 terraform.tfvars 자동 생성 스크립트
# 사용법: ./generate-tfvars.sh

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 스크립트 시작
log_info "AWS Load Balancer Controller Helm Chart 배포를 위한 terraform.tfvars 파일을 생성합니다..."

# Terraform 디렉토리 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../walb_terraform"
TFVARS_FILE="$SCRIPT_DIR/terraform.tfvars"

# Terraform 디렉토리 존재 확인
if [ ! -d "$TERRAFORM_DIR" ]; then
    log_error "Terraform 디렉토리를 찾을 수 없습니다: $TERRAFORM_DIR"
    log_info "현재 디렉토리: $(pwd)"
    log_info "스크립트를 helm-lbc 디렉토리에서 실행해주세요."
    exit 1
fi

# terraform output으로부터 값 가져오기
log_info "Terraform 인프라 정보를 가져오는 중..."

cd "$TERRAFORM_DIR"

# Terraform 초기화 및 상태 확인 (S3 backend 지원)
log_info "Terraform 초기화 중..."
log_info "현재 작업 디렉토리: $(pwd)"
log_info "Terraform 디렉토리: $TERRAFORM_DIR"

INIT_OUTPUT=$(terraform init -input=false 2>&1)
if [ $? -ne 0 ]; then
    log_error "Terraform 초기화에 실패했습니다."
    log_error "에러 메시지: $INIT_OUTPUT"
    log_info "AWS 자격증명과 S3 backend 설정을 확인해주세요."
    exit 1
fi

# Remote state 존재 확인
log_info "Remote state 확인 중..."
if ! terraform state list >/dev/null 2>&1; then
    log_error "Terraform state를 찾을 수 없습니다."
    log_info "먼저 terraform apply를 실행하여 인프라를 배포해주세요."
    exit 1
fi

# Terraform output 실행 및 JSON 파싱
log_info "Terraform outputs 가져오는 중..."

# 필요한 값들을 개별적으로 가져오기 (jq 없이)
CLUSTER_NAME=$(terraform output -json eks_cluster_info 2>/dev/null | grep -o '"cluster_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"cluster_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
VPC_ID=$(terraform output -json vpc_info 2>/dev/null | grep -o '"vpc_id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"vpc_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
AWS_REGION=$(terraform output -json deployment_info 2>/dev/null | grep -o '"aws_region"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"aws_region"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "ap-northeast-2")
PROJECT_NAME=$(terraform output -json deployment_info 2>/dev/null | grep -o '"project_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"project_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "walb-app")

# 값 검증
if [ -z "$CLUSTER_NAME" ] || [ "$CLUSTER_NAME" = "null" ]; then
    log_error "EKS 클러스터 이름을 가져올 수 없습니다."
    log_info "terraform output eks_cluster_info 명령어를 확인해주세요."
    exit 1
fi

if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "null" ]; then
    log_error "VPC ID를 가져올 수 없습니다."
    log_info "terraform output vpc_info 명령어를 확인해주세요."
    exit 1
fi

log_success "인프라 정보 수집 완료:"
log_info "  - 프로젝트 이름: $PROJECT_NAME"
log_info "  - AWS 리전: $AWS_REGION"
log_info "  - EKS 클러스터: $CLUSTER_NAME"
log_info "  - VPC ID: $VPC_ID"

# terraform.tfvars 파일 생성
cd "$SCRIPT_DIR"

log_info "terraform.tfvars 파일을 생성하는 중..."

cat > "$TFVARS_FILE" << EOF
# AWS Load Balancer Controller Helm 배포를 위한 변수 값
# 자동 생성됨: $(date)

# 기본 정보 (terraform output에서 자동 수집)
project_name = "$PROJECT_NAME"
environment  = "dev"
aws_region   = "$AWS_REGION"

# EKS 클러스터 정보 (terraform output에서 자동 수집)
cluster_name = "$CLUSTER_NAME"
vpc_id       = "$VPC_ID"

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
  Timestamp  = "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# 파일 생성 확인
if [ -f "$TFVARS_FILE" ]; then
    log_success "terraform.tfvars 파일이 성공적으로 생성되었습니다:"
    log_info "  파일 위치: $TFVARS_FILE"
    log_info "  파일 크기: $(wc -c < "$TFVARS_FILE") bytes"
    
    echo ""
    log_info "생성된 terraform.tfvars 파일 내용:"
    echo "----------------------------------------"
    cat "$TFVARS_FILE"
    echo "----------------------------------------"
    
    echo ""
    log_info "다음 단계:"
    log_info "1. 생성된 terraform.tfvars 파일의 값들을 검토하세요"
    log_info "2. 필요시 값들을 수정하세요"
    log_info "3. terraform init && terraform plan && terraform apply 를 실행하세요"
    
    echo ""
    log_warning "주의사항:"
    log_warning "- 이 파일은 자동 생성되었습니다."
    log_warning "- 필요에 따라 값들을 수정할 수 있습니다."
    log_warning "- 인프라 변경 시 이 스크립트를 다시 실행하세요."
    
else
    log_error "terraform.tfvars 파일 생성에 실패했습니다."
    exit 1
fi

log_success "스크립트 실행 완료!"