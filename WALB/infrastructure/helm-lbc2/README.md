# AWS Load Balancer Controller Helm 배포 (App2 전용)

이 디렉토리는 Terraform2에서 생성된 EKS 인프라를 기반으로 AWS Load Balancer Controller를 Helm으로 배포하는 App2 전용 구성입니다.

## 📋 전제 조건

1. **Terraform2 인프라 완료**: 메인 terraform2 디렉토리에서 `terraform apply` 완료
2. **필수 리소스 생성 확인**:
   - EKS 클러스터 (walb2-eks-cluster)
   - VPC 및 서브넷
   - OIDC Provider
   - IAM Role 및 Policy
   - ServiceAccount (aws-load-balancer-controller-app2)
   - RBAC 리소스 (ClusterRole, ClusterRoleBinding)

## 🚀 사용 방법

### 1단계: 변수 파일 설정

```bash
# 예시 파일을 실제 변수 파일로 복사
cp terraform.tfvars.example terraform.tfvars

# terraform2 output에서 필요한 값들을 확인
cd ../terraform2
terraform output eks_cluster_info
terraform output vpc_info

# terraform.tfvars 파일 편집
vi terraform.tfvars
```

### 2단계: Terraform 초기화

```bash
cd helm-lbc2
terraform init
```

### 3단계: 배포 계획 확인

```bash
terraform plan
```

### 4단계: AWS Load Balancer Controller 배포 (App2 전용)

```bash
terraform apply
```

### 5단계: 배포 확인

```bash
# 배포 상태 확인
terraform output

# Pod 상태 확인
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# 서비스 확인
kubectl get deployment -n kube-system aws-load-balancer-controller

# App2 전용 IngressClass 확인
kubectl get ingressclass alb-app2

# 모든 IngressClass 확인
kubectl get ingressclass

# 로그 확인
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## 📁 파일 구조

```
helm-lbc2/
├── providers.tf           # Provider 설정 (Helm, Kubernetes, AWS) - App2 전용
├── variables.tf           # 입력 변수 정의 - App2 전용 변수 포함
├── main.tf               # Helm Chart 배포 리소스 - App2 전용 설정
├── outputs.tf            # 출력값 정의 - App2 전용 정보
├── terraform.tfvars.example  # 변수 값 예시 - App2 전용
└── README.md             # 이 파일
```

## 🎯 App2 전용 설정

### IngressClass 설정
- **이름**: `alb-app2` (App1과 구분)
- **기본값**: `false` (App1이 기본값)
- **목적**: App1과 App2의 ALB를 분리하여 관리

### ServiceAccount
- **이름**: `aws-load-balancer-controller-app2`
- **네임스페이스**: `kube-system`
- **IAM Role**: App2 전용 IAM Role과 연결

### Helm Release
- **이름**: `walb-app2-alb-controller`
- **차트**: `aws-load-balancer-controller` (동일)
- **버전**: `1.8.1`

## 🔧 주요 특징

### App1과의 차이점
1. **ServiceAccount**: `aws-load-balancer-controller-app2` (App1과 분리)
2. **IngressClass**: `alb-app2` (App1은 `alb`)
3. **Helm Release 이름**: `walb-app2-alb-controller`
4. **기본 IngressClass**: `false` (App1이 기본값)

### 공통점
- 동일한 클러스터에서 실행
- 동일한 Controller 이미지 사용
- 동일한 네임스페이스 (`kube-system`) 사용

## 🚨 주의사항

1. **순서 중요**: 반드시 terraform2 먼저, helm-lbc2 나중에 실행
2. **App1과 충돌 방지**: 다른 ServiceAccount와 IngressClass 사용
3. **변수 설정**: `terraform.tfvars`에 App2 전용 값 입력 필수
4. **Webhook 패치**: App1에서 이미 패치했다면 중복 패치 방지
5. **클러스터 공유**: App1과 동일한 클러스터 사용 시 리소스 충돌 주의

## 🔍 문제 해결

### Controller Pod 충돌
```bash
# 두 개의 Controller가 실행되는지 확인
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# ServiceAccount 확인
kubectl get serviceaccount -n kube-system | grep aws-load-balancer-controller
```

### IngressClass 확인
```bash
# 모든 IngressClass 확인
kubectl get ingressclass

# App2 전용 IngressClass 확인
kubectl describe ingressclass alb-app2
```

### ServiceAccount 문제
```bash
# App2 ServiceAccount 확인
kubectl get serviceaccount aws-load-balancer-controller-app2 -n kube-system

# 메인 terraform2에서 다시 적용 필요
cd ../terraform2
terraform apply
```

## 📚 참고 자료

- [AWS Load Balancer Controller 공식 문서](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Helm Chart 문서](https://github.com/aws/eks-charts/tree/master/stable/aws-load-balancer-controller)
- [EKS 공식 가이드](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)
- [Multiple IngressClass 설정 가이드](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.8/guide/ingress/ingress_class/)