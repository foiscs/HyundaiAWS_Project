# AWS Load Balancer Controller Helm 배포 출력값 (App2 전용)

output "helm_release_info" {
  description = "Helm 릴리스 정보 (App2)"
  value = {
    name      = helm_release.aws_load_balancer_controller_app2.name
    namespace = helm_release.aws_load_balancer_controller_app2.namespace
    version   = helm_release.aws_load_balancer_controller_app2.version
    status    = helm_release.aws_load_balancer_controller_app2.status
    chart     = helm_release.aws_load_balancer_controller_app2.chart
  }
}

output "cluster_info" {
  description = "클러스터 정보 (App2)"
  value = {
    cluster_name = var.cluster_name
    vpc_id       = var.vpc_id
    region       = var.aws_region
  }
}

output "ingress_class_info" {
  description = "IngressClass 정보 (App2 전용)"
  value = {
    name                = var.ingress_class_name
    default_class       = var.default_ingress_class
    service_account     = var.service_account_name
  }
}

output "verification_commands" {
  description = "설치 확인 명령어 (App2)"
  value = {
    check_pods         = "kubectl get pods -n ${var.namespace} -l app.kubernetes.io/name=aws-load-balancer-controller"
    check_deployment   = "kubectl get deployment -n ${var.namespace} aws-load-balancer-controller"
    check_logs        = "kubectl logs -n ${var.namespace} -l app.kubernetes.io/name=aws-load-balancer-controller"
    check_ingressclass = "kubectl get ingressclass ${var.ingress_class_name}"
    check_webhook     = "kubectl get validatingwebhookconfigurations aws-load-balancer-webhook"
    check_all_ingressclasses = "kubectl get ingressclass"
  }
}

output "service_account_info" {
  description = "ServiceAccount 정보 (Terraform2에서 생성됨)"
  value = {
    name        = data.kubernetes_service_account.aws_load_balancer_controller_app2.metadata[0].name
    namespace   = data.kubernetes_service_account.aws_load_balancer_controller_app2.metadata[0].namespace
    annotations = data.kubernetes_service_account.aws_load_balancer_controller_app2.metadata[0].annotations
  }
  sensitive = true
}

output "deployment_status" {
  description = "배포 상태 요약 (App2)"
  value = {
    helm_status          = helm_release.aws_load_balancer_controller_app2.status
    service_account_name = var.service_account_name
    namespace           = var.namespace
    chart_version       = var.chart_version
    replica_count       = var.replica_count
    ingress_class_name  = var.ingress_class_name
    default_ingress_class = var.default_ingress_class
    webhook_patched     = var.webhook_failure_policy == "Ignore" ? true : false
  }
}