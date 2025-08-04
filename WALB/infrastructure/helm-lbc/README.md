# AWS Load Balancer Controller Helm 배포

이 디렉토리는 Terraform에서 생성된 EKS 인프라를 기반으로 AWS Load Balancer Controller를 Helm으로 배포하는 전용 구성입니다.

## 📋 전제 조건

1. **Terraform 인프라 완료**: 메인 terraform 디렉토리에서 `terraform apply` 완료
2. **필수 리소스 생성 확인**:
   - EKS 클러스터
   - VPC 및 서브넷
   - OIDC Provider
   - IAM Role 및 Policy
   - ServiceAccount
   - RBAC 리소스 (ClusterRole, ClusterRoleBinding)

## 🚀 사용 방법

### 1단계: 변수 파일 설정

```bash
# 예시 파일을 실제 변수 파일로 복사
cp terraform.tfvars.example terraform.tfvars

# terraform output에서 필요한 값들을 확인
cd ../walb_terraform
terraform output eks_cluster_info
terraform output vpc_info

# terraform.tfvars 파일 편집
vi terraform.tfvars
```

### 2단계: Terraform 초기화

```bash
cd helm-lbc
terraform init
```

### 3단계: 배포 계획 확인

```bash
terraform plan
```

### 4단계: AWS Load Balancer Controller 배포

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

# IngressClass 확인
kubectl get ingressclass

# 로그 확인
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## 📁 파일 구조

```
helm-lbc/
├── providers.tf           # Provider 설정 (Helm, Kubernetes, AWS)
├── variables.tf           # 입력 변수 정의
├── main.tf               # Helm Chart 배포 리소스
├── outputs.tf            # 출력값 정의
├── terraform.tfvars.example  # 변수 값 예시
└── README.md             # 이 파일
```

## 🔧 주요 설정

- **Helm Chart**: `aws-load-balancer-controller` (v1.8.1)
- **Repository**: https://aws.github.io/eks-charts
- **ServiceAccount**: 기존 생성된 것 사용 (create=false)
- **IngressClass**: 자동 생성 및 기본값으로 설정
- **Webhook**: 자동 패치 (타임아웃 30초, 실패 정책 Ignore)

## 🎯 주요 기능

### 자동화된 설정
- EKS 클러스터 자동 연결
- 기존 ServiceAccount 자동 감지
- IngressClass 자동 생성
- ValidatingWebhookConfiguration 자동 패치

### 리소스 관리
- Pod Anti-Affinity로 고가용성 보장
- PodDisruptionBudget으로 안정성 확보
- 리소스 요청/제한 설정

### 보안 설정
- 비-루트 사용자로 실행
- 최소 권한 원칙 적용
- 자체 서명 인증서 사용

## 🚨 주의사항

1. **순서 중요**: 반드시 메인 terraform 적용 후 실행
2. **변수 설정**: `terraform.tfvars`에 올바른 값 입력 필수
3. **권한 확인**: AWS 및 Kubernetes 접근 권한 확인
4. **네트워킹**: 클러스터 엔드포인트 접근 가능한지 확인

## 🔍 문제 해결

### Helm 배포 실패
```bash
# Helm 상태 확인
helm list -n kube-system

# 실패한 릴리스 삭제
helm uninstall aws-load-balancer-controller -n kube-system

# 다시 시도
terraform apply
```

### ServiceAccount 찾을 수 없음
```bash
# ServiceAccount 확인
kubectl get serviceaccount aws-load-balancer-controller -n kube-system

# 메인 terraform에서 다시 적용 필요
cd ../walb_terraform
terraform apply
```

### Pod 시작 실패
```bash
# Pod 상태 확인
kubectl describe pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# 로그 확인
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## 📚 참고 자료

- [AWS Load Balancer Controller 공식 문서](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Helm Chart 문서](https://github.com/aws/eks-charts/tree/master/stable/aws-load-balancer-controller)
- [EKS 공식 가이드](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)