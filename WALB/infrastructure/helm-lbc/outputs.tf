# AWS Load Balancer Controller Helm 배포 출력값

output "helm_release_info" {
  description = "Helm 릴리스 정보"
  value = {
    name      = helm_release.aws_load_balancer_controller.name
    namespace = helm_release.aws_load_balancer_controller.namespace
    version   = helm_release.aws_load_balancer_controller.version
    status    = helm_release.aws_load_balancer_controller.status
    chart     = helm_release.aws_load_balancer_controller.chart
  }
}

output "cluster_info" {
  description = "클러스터 정보"
  value = {
    cluster_name = var.cluster_name
    vpc_id       = var.vpc_id
    region       = var.aws_region
  }
}

output "verification_commands" {
  description = "설치 확인 명령어"
  value = {
    check_pods        = "kubectl get pods -n ${var.namespace} -l app.kubernetes.io/name=aws-load-balancer-controller"
    check_deployment  = "kubectl get deployment -n ${var.namespace} aws-load-balancer-controller"
    check_logs        = "kubectl logs -n ${var.namespace} -l app.kubernetes.io/name=aws-load-balancer-controller"
    check_ingressclass = "kubectl get ingressclass"
    check_webhook     = "kubectl get validatingwebhookconfigurations aws-load-balancer-webhook"
  }
}

output "service_account_info" {
  description = "ServiceAccount 정보 (Terraform에서 생성됨)"
  value = {
    name        = data.kubernetes_service_account.aws_load_balancer_controller.metadata[0].name
    namespace   = data.kubernetes_service_account.aws_load_balancer_controller.metadata[0].namespace
    annotations = data.kubernetes_service_account.aws_load_balancer_controller.metadata[0].annotations
  }
  sensitive = true
}

output "deployment_status" {
  description = "배포 상태 요약"
  value = {
    helm_status          = helm_release.aws_load_balancer_controller.status
    service_account_name = var.service_account_name
    namespace           = var.namespace
    chart_version       = var.chart_version
    replica_count       = var.replica_count
    webhook_patched     = var.webhook_failure_policy == "Ignore" ? true : false
  }
}