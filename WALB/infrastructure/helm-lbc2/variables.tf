# Helm LBC2 설치를 위한 변수 정의 (App2 전용)

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "walb2-app"
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "cluster_name" {
  description = "EKS 클러스터 이름"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "service_account_name" {
  description = "AWS Load Balancer Controller ServiceAccount 이름 (App2 전용)"
  type        = string
  default     = "aws-load-balancer-controller-app2"
}

variable "namespace" {
  description = "AWS Load Balancer Controller를 설치할 네임스페이스"
  type        = string
  default     = "kube-system"
}

variable "chart_version" {
  description = "AWS Load Balancer Controller Helm Chart 버전"
  type        = string
  default     = "1.8.1"
}

variable "replica_count" {
  description = "AWS Load Balancer Controller 복제본 수"
  type        = number
  default     = 2
}

variable "image_repository" {
  description = "AWS Load Balancer Controller 이미지 리포지토리"
  type        = string
  default     = "602401143452.dkr.ecr.ap-northeast-2.amazonaws.com/amazon/aws-load-balancer-controller"
}

variable "ingress_class_name" {
  description = "IngressClass 이름 (App2 전용)"
  type        = string
  default     = "alb-app2"
}

variable "default_ingress_class" {
  description = "기본 IngressClass로 설정할지 여부"
  type        = bool
  default     = false  # App2는 기본값이 아님
}

variable "enable_shield" {
  description = "AWS Shield 기능 활성화"
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "AWS WAF 기능 활성화"
  type        = bool
  default     = false
}

variable "enable_wafv2" {
  description = "AWS WAFv2 기능 활성화"
  type        = bool
  default     = false
}

variable "log_level" {
  description = "로그 레벨"
  type        = string
  default     = "info"
  
  validation {
    condition     = contains(["debug", "info", "warn", "error"], var.log_level)
    error_message = "로그 레벨은 debug, info, warn, error 중 하나여야 합니다."
  }
}

variable "webhook_timeout_seconds" {
  description = "Webhook 타임아웃 시간 (초)"
  type        = number
  default     = 30
}

variable "webhook_failure_policy" {
  description = "Webhook 실패 정책"
  type        = string
  default     = "Ignore"
  
  validation {
    condition     = contains(["Ignore", "Fail"], var.webhook_failure_policy)
    error_message = "Webhook 실패 정책은 Ignore 또는 Fail이어야 합니다."
  }
}

variable "resource_limits_cpu" {
  description = "CPU 리소스 제한"
  type        = string
  default     = "1000m"
}

variable "resource_limits_memory" {
  description = "메모리 리소스 제한"
  type        = string
  default     = "2Gi"
}

variable "resource_requests_cpu" {
  description = "CPU 리소스 요청"
  type        = string
  default     = "500m"
}

variable "resource_requests_memory" {
  description = "메모리 리소스 요청"
  type        = string
  default     = "1Gi"
}

variable "additional_tags" {
  description = "추가 태그"
  type        = map(string)
  default     = {}
}