variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "walb2"
}
variable "environment" {
  description = "환경 (dev, staging, prod, walb2)"
  type        = string
  default     = "walb2"
  validation {
    condition     = contains(["dev", "staging", "prod", "walb2"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

# =========================================
# VPC 네트워크 설정
# =========================================
variable "vpc_name" {
  description = "VPC name"
  type        = string
  default     = "simon-test"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "프라이빗 서브넷 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}
variable "database_subnets" {
  description = "데이터베이스 서브넷 CIDR 블록들"
  type        = list(string)
  default     = [
    "10.0.20.0/24",
    "10.0.21.0/24"
  ]
}
# =========================================
# RDS 데이터베이스 설정
# =========================================
variable "rds_instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "데이터베이스 이름"
  type        = string
  default     = "walb2_DB"
}

variable "db_username" {
  description = "데이터베이스 사용자명"
  type        = string
  default     = "msadmin"
}

variable "db_password" {
  description = "데이터베이스 비밀번호"
  type        = string
  sensitive   = true
  default     = "password123!"
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "253157413163.dkr.ecr.ap-northeast-2.amazonaws.com/walb2-app-ecr"
}
# =========================================
# EKS 클러스터 설정
# =========================================
variable "cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
  default     = ""  # 자동으로 project_name-environment-eks로 생성
}

variable "ec2_key_pair_name" {
  description = "EKS 노드 그룹 SSH 접근용 키 페어 이름"
  type        = string
  default     = null
}

variable "allowed_ssh_cidrs" {
  description = "SSH 접근을 허용할 CIDR 블록들"
  type        = list(string)
  default     = ["10.0.0.0/16"]  # VPC 내부만 허용
}
variable "eks_cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.33"
}

variable "node_group_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_group_min_size" {
  description = "Minimum size of the node group"
  type        = number
  default     = 1
}

variable "node_group_max_size" {
  description = "Maximum size of the node group"
  type        = number
  default     = 3
}

variable "node_group_desired_size" {
  description = "Desired size of the node group"
  type        = number
  default     = 2
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log group retention in days"
  type        = number
  default     = 1
}

variable "lb_controller_iam_role_name" {
  description = "IAM role name for load balancer controller"
  type        = string
  default     = "inhouse-eks-aws-lb-ctrl"
}

variable "lb_controller_service_account_name" {
  description = "Service account name for load balancer controller"
  type        = string
  default     = "aws-load-balancer-controller"
}

variable "lb_controller_image_repository" {
  description = "Image repository for load balancer controller"
  type        = string
  default     = "602401143452.dkr.ecr.ap-northeast-2.amazonaws.com/amazon/aws-load-balancer-controller"
}