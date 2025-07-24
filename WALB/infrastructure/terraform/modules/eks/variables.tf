# infrastructure/terraform/modules/eks/variables.tf
# EKS 모듈 변수 정의

# 필수 변수
variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
}

variable "cluster_version" {
  description = "EKS 클러스터 버전"
  type        = string
  default     = "1.32"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "EKS 클러스터용 서브넷 ID 목록"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "EKS 노드 그룹이 사용하는 프라이빗 서브넷 ID 목록"
  type        = list(string)
}

# 클러스터 엔드포인트 설정
variable "cluster_endpoint_private_access" {
  description = "EKS 클러스터 프라이빗 엔드포인트 활성화 여부"
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access" {
  description = "EKS 클러스터 퍼블릭 엔드포인트 활성화 여부"
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "퍼블릭 엔드포인트 접근 허용 CIDR"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "cluster_endpoint_private_access_cidrs" {
  description = "프라이빗 엔드포인트 접근 허용 CIDR"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

# 로깅 설정
variable "cluster_enabled_log_types" {
  description = "활성화할 클러스터 로그 타입"
  type        = list(string)
  default     = ["api", "audit", "authenticator"]
}

variable "log_retention_days" {
  description = "CloudWatch 로그 보관 일수"
  type        = number
  default     = 30
}

# KMS 설정
variable "kms_deletion_window" {
  description = "KMS 키 삭제 대기 기간 (일)"
  type        = number
  default     = 7
}

# IRSA 설정
variable "enable_irsa" {
  description = "OIDC 기반 IAM 역할 사용 여부"
  type        = bool
  default     = true
}

# 노드 그룹 설정
variable "node_group_name" {
  description = "EKS 노드 그룹 이름"
  type        = string
  default     = "main-nodes"
}

variable "eks_node_instance_types" {
  description = "EKS 노드 그룹 인스턴스 타입"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "capacity_type" {
  description = "노드 그룹의 용량 타입 (ON_DEMAND 또는 SPOT)"
  type        = string
  default     = "ON_DEMAND"
  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.capacity_type)
    error_message = "Capacity type must be ON_DEMAND or SPOT."
  }
}

variable "ami_type" {
  description = "EKS 노드 그룹에서 사용할 AMI 타입"
  type        = string
  default     = "AL2_x86_64"
}

# 스케일링 설정
variable "eks_node_desired_capacity" {
  description = "EKS 노드 그룹 희망 용량"
  type        = number
  default     = 2
}

variable "eks_node_max_capacity" {
  description = "EKS 노드 그룹 최대 용량"
  type        = number
  default     = 4
}

variable "eks_node_min_capacity" {
  description = "EKS 노드 그룹 최소 용량"
  type        = number
  default     = 1
}

variable "max_unavailable_percentage" {
  description = "업데이트 시 동시에 사용할 수 없는 노드 비율 (%)"
  type        = number
  default     = 50
}

# SSH 접근 설정
variable "enable_ssh_access" {
  description = "SSH 접근 활성화 여부"
  type        = bool
  default     = false
}

variable "ec2_key_pair_name" {
  description = "EC2 키 페어 이름"
  type        = string
  default     = null
}

variable "ssh_access_cidrs" {
  description = "SSH 접근 허용 CIDR 블록"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

# 시작 템플릿 설정
variable "create_launch_template" {
  description = "Launch template 생성 여부"
  type        = bool
  default     = true
}

variable "ebs_volume_type" {
  description = "EBS 볼륨 타입"
  type        = string
  default     = "gp3"
}

variable "ebs_volume_size" {
  description = "EBS 볼륨 크기 (GB)"
  type        = number
  default     = 30
}

# 노드 그룹 테인트 설정
variable "node_group_taints" {
  description = "EKS 노드 그룹에 적용할 taint 목록"
  type = map(object({
    key    = string
    value  = string
    effect = string
  }))
  default = {}
}

# EKS 애드온 설정
variable "enable_vpc_cni_addon" {
  description = "vpc-cni EKS addon 활성화 여부"
  type        = bool
  default     = true
}

variable "enable_coredns_addon" {
  description = "CoreDNS 애드온 활성화 여부"
  type        = bool
  default     = true
}

variable "enable_kube_proxy_addon" {
  description = "kube-proxy 애드온 활성화 여부"
  type        = bool
  default     = true
}

variable "vpc_cni_addon_version" {
  description = "VPC CNI 애드온 버전"
  type        = string
  default     = null
}

variable "coredns_addon_version" {
  description = "CoreDNS 애드온 버전"
  type        = string
  default     = null
}

variable "kube_proxy_addon_version" {
  description = "kube-proxy 애드온 버전"
  type        = string
  default     = null
}

# Load Balancer Controller 설정
variable "enable_load_balancer" {
  description = "AWS Load Balancer Controller 활성화 여부"
  type        = bool
  default     = false
}

variable "use_existing_load_balancer_policy" {
  description = "기존 Load Balancer Controller 정책 사용 여부"
  type        = bool
  default     = false
}

# AWS Auth 설정
variable "map_roles" {
  description = "추가로 매핑할 IAM 역할 목록"
  type = list(object({
    rolearn  = string
    username = string
    groups   = list(string)
  }))
  default = []
}

variable "map_users" {
  description = "추가로 매핑할 IAM 사용자 목록"
  type = list(object({
    userarn  = string 
    username = string
    groups   = list(string)
  }))
  default = []
}

variable "cluster_admin_users" {
  description = "클러스터 관리자 권한을 가질 IAM 사용자 ARN 목록"
  type = list(string)
  default = []
}

variable "cluster_admin_roles" {
  description = "클러스터 관리자 권한을 가질 IAM 역할 ARN 목록"
  type = list(string)
  default = []
}

# 태그
variable "common_tags" {
  description = "리소스 태그"
  type        = map(string)
  default     = {}
}