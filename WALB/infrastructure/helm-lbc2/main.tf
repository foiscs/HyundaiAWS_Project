# AWS Load Balancer Controller Helm Chart 배포 (App2 전용)
# Terraform2에서 생성된 리소스들을 활용

locals {
  common_labels = {
    "app.kubernetes.io/name"       = "aws-load-balancer-controller"
    "app.kubernetes.io/instance"   = var.project_name
    "app.kubernetes.io/managed-by" = "Terraform-Helm"
    "app.kubernetes.io/component"  = "load-balancer-controller-app2"
  }
  
  common_tags = merge({
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform-Helm"
    Component   = "LoadBalancerController-App2"
  }, var.additional_tags)
}

# 기존 ServiceAccount 확인 (Terraform2에서 생성됨)
data "kubernetes_service_account" "aws_load_balancer_controller_app2" {
  metadata {
    name      = var.service_account_name
    namespace = var.namespace
  }
}

# AWS Load Balancer Controller Helm Release (App2 전용)
resource "helm_release" "aws_load_balancer_controller_app2" {
  name       = "walb-app2-alb-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = var.namespace
  version    = var.chart_version

  # 기본 설정
  set {
    name  = "clusterName"
    value = var.cluster_name
  }

  set {
    name  = "region"
    value = var.aws_region
  }

  set {
    name  = "vpcId"
    value = var.vpc_id
  }

  # ServiceAccount 설정 (Terraform2에서 이미 생성됨)
  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = var.service_account_name
  }

  # 이미지 설정
  set {
    name  = "image.repository"
    value = var.image_repository
  }

  set {
    name  = "image.tag"
    value = "v2.8.1"
  }

  # 복제본 수
  set {
    name  = "replicaCount"
    value = var.replica_count
  }

  # cert-manager 사용 비활성화 (자체 서명 인증서 사용)
  set {
    name  = "enableCertManager"
    value = "false"
  }

  # App2 전용 IngressClass 설정
  set {
    name  = "createIngressClassResource"
    value = "true"
  }

  set {
    name  = "ingressClass"
    value = var.ingress_class_name
  }

  set {
    name  = "defaultIngressClass"
    value = var.default_ingress_class
  }

  # IngressClass가 기본값이 아님을 명시
  set {
    name  = "ingressClassConfig.default"
    value = "false"
  }

  # 리소스 설정
  set {
    name  = "resources.limits.cpu"
    value = var.resource_limits_cpu
  }

  set {
    name  = "resources.limits.memory"
    value = var.resource_limits_memory
  }

  set {
    name  = "resources.requests.cpu"
    value = var.resource_requests_cpu
  }

  set {
    name  = "resources.requests.memory"
    value = var.resource_requests_memory
  }

  # 로깅 설정
  set {
    name  = "logLevel"
    value = var.log_level
  }

  # AWS 기능 설정
  set {
    name  = "enableShield"
    value = var.enable_shield
  }

  set {
    name  = "enableWaf"
    value = var.enable_waf
  }

  set {
    name  = "enableWafv2"
    value = var.enable_wafv2
  }

  # Node Selector (Linux 노드에만 배치)
  set {
    name  = "nodeSelector.kubernetes\\.io/os"
    value = "linux"
  }

  # 보안 설정
  set {
    name  = "securityContext.fsGroup"
    value = "65534"
  }

  set {
    name  = "securityContext.runAsNonRoot"
    value = "true"
  }

  # 공통 라벨 설정
  set {
    name  = "commonLabels.app\\.kubernetes\\.io/managed-by"
    value = "Terraform-Helm"
  }

  set {
    name  = "commonLabels.app\\.kubernetes\\.io/instance"
    value = var.project_name
  }

  # finalizer 관리 설정
  set {
    name  = "enableFinalizer"
    value = "true"
  }

  # PodDisruptionBudget 설정
  set {
    name  = "podDisruptionBudget.enabled"
    value = "true"
  }

  set {
    name  = "podDisruptionBudget.minAvailable"
    value = "1"
  }

  # 웹훅 설정
  set {
    name  = "webhook.certManager.enabled"
    value = "false"
  }

  set {
    name  = "webhook.port"
    value = "9443"
  }

  # 웹훅 리소스 설정
  set {
    name  = "webhook.resources.limits.cpu"
    value = var.resource_limits_cpu
  }

  set {
    name  = "webhook.resources.limits.memory"
    value = "1Gi"
  }

  set {
    name  = "webhook.resources.requests.cpu"
    value = var.resource_requests_cpu
  }

  set {
    name  = "webhook.resources.requests.memory"
    value = "512Mi"
  }

  # Pod Anti-Affinity 설정 (가용성 향상)
  set {
    name  = "affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].weight"
    value = "100"
  }

  set {
    name  = "affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].podAffinityTerm.labelSelector.matchExpressions[0].key"
    value = "app.kubernetes.io/name"
  }

  set {
    name  = "affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].podAffinityTerm.labelSelector.matchExpressions[0].operator"
    value = "In"
  }

  set {
    name  = "affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].podAffinityTerm.labelSelector.matchExpressions[0].values[0]"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].podAffinityTerm.topologyKey"
    value = "kubernetes.io/hostname"
  }

  # 설치 옵션
  timeout         = 600
  wait            = true
  wait_for_jobs   = true
  atomic          = true
  cleanup_on_fail = true
  replace         = false

  # 의존성 확인
  depends_on = [
    data.kubernetes_service_account.aws_load_balancer_controller_app2
  ]
}

# ValidatingWebhookConfiguration 패치 (선택사항)
# 주의: 이미 App1에서 패치했다면 중복 패치 방지 필요
resource "null_resource" "webhook_patch_app2" {
  count = var.webhook_failure_policy == "Ignore" ? 1 : 0

  provisioner "local-exec" {
    command = <<-EOT
      # Wait for webhook configuration to be created
      echo "ValidatingWebhookConfiguration 패치 대기 중... (App2)"
      timeout 300 bash -c 'while ! kubectl get validatingwebhookconfigurations aws-load-balancer-webhook >/dev/null 2>&1; do sleep 5; done'
      
      # Check if already patched to avoid duplicate patching
      current_policy=$(kubectl get validatingwebhookconfigurations aws-load-balancer-webhook -o jsonpath='{.webhooks[0].failurePolicy}' 2>/dev/null || echo "")
      
      if [ "$current_policy" != "${var.webhook_failure_policy}" ]; then
        echo "ValidatingWebhookConfiguration 패치 적용 중... (App2)"
        kubectl patch validatingwebhookconfigurations aws-load-balancer-webhook --type='json' -p='[
          {
            "op": "replace",
            "path": "/webhooks/0/timeoutSeconds",
            "value": ${var.webhook_timeout_seconds}
          },
          {
            "op": "replace", 
            "path": "/webhooks/0/failurePolicy",
            "value": "${var.webhook_failure_policy}"
          },
          {
            "op": "replace",
            "path": "/webhooks/1/timeoutSeconds", 
            "value": ${var.webhook_timeout_seconds}
          },
          {
            "op": "replace",
            "path": "/webhooks/1/failurePolicy",
            "value": "${var.webhook_failure_policy}"
          }
        ]'
        echo "ValidatingWebhookConfiguration 패치 완료 (App2)"
      else
        echo "ValidatingWebhookConfiguration 이미 패치됨 (App2)"
      fi
    EOT
  }

  depends_on = [helm_release.aws_load_balancer_controller_app2]
  
  triggers = {
    helm_release_version = helm_release.aws_load_balancer_controller_app2.version
    webhook_config      = "${var.webhook_timeout_seconds}-${var.webhook_failure_policy}"
  }
}