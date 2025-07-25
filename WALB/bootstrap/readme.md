# Terraform Backend Bootstrap

이 디렉토리는 WALB 프로젝트의 Terraform backend 리소스(S3 버킷, DynamoDB 테이블)를 생성하기 위한 bootstrap 구성입니다.

## 🎯 목적

Terraform state를 저장할 S3 버킷과 state lock을 위한 DynamoDB 테이블을 **한 번만** 생성합니다.

## 📁 파일 구조

```
bootstrap/
├── main.tf           # 주요 리소스 정의 (S3, DynamoDB, KMS)
├── providers.tf      # Terraform 및 AWS provider 설정
├── variables.tf      # 입력 변수 정의
├── outputs.tf        # 출력 값 정의
├── terraform.tfvars  # 변수 값 설정
└── README.md        # 이 파일
```

## 🚀 실행 방법

### 1단계: Bootstrap 실행 (한 번만)

```bash
# bootstrap 디렉토리로 이동
cd WALB/bootstrap

# Terraform 초기화 (로컬 state 사용)
terraform init

# 실행 계획 확인
terraform plan

# 리소스 생성
terraform apply
```

### 2단계: 출력 정보 확인

```bash
# 생성된 리소스 정보 확인
terraform output

# backend 설정 정보만 확인
terraform output backend_configuration
```

### 3단계: 메인 인프라에 backend 설정 적용

출력된 정보를 사용하여 `WALB/infrastructure/terraform/providers.tf`에 backend 설정을 추가:

```hcl
terraform {
  backend "s3" {
    bucket         = "walb-terraform-state-XXXX"  # 출력에서 확인
    key            = "infrastructure/terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "walb-terraform-lock-XXXX"   # 출력에서 확인
    kms_key_id     = "arn:aws:kms:..."            # 출력에서 확인
  }
}
```

## 🔒 생성되는 리소스

### S3 버킷
- **이름**: `walb-terraform-state-{계정ID뒤4자리}`
- **기능**: Terraform state 파일 저장
- **보안**: 
  - 버전 관리 활성화
  - AES256 암호화
  - 퍼블릭 액세스 차단
  - HTTPS 강제

### DynamoDB 테이블
- **이름**: `walb-terraform-lock-{계정ID뒤4자리}`
- **기능**: Terraform state 잠금
- **설정**:
  - PAY_PER_REQUEST 모드 (비용 효율적)
  - Point-in-time recovery 활성화
  - 서버 사이드 암호화 활성화

### KMS 키
- **목적**: 추가 암호화 레이어 제공
- **기능**: 
  - 키 자동 순환 활성화
  - Terraform 역할에만 접근 권한 부여

### CloudTrail (선택사항)
- **목적**: State 버킷 접근 감사
- **로깅**: 모든 S3 API 호출 기록

## 💰 예상 비용

최소 사용량 기준 월 $1-2 USD:
- S3 Storage: ~$0.05
- KMS 키: $1.00
- DynamoDB: 사용량에 따라 (보통 $0.01 미만)
- CloudTrail: 사용량에 따라

## 🔧 커스터마이징

### terraform.tfvars 수정

```hcl
# 리전 변경
aws_region = "us-west-2"

# 라이프사이클 정책 조정
state_bucket_lifecycle_days = 180

# 보안 설정 조정
enable_mfa_requirement = true
enable_cloudtrail_monitoring = false
```

### 보안 강화 옵션

1. **MFA 요구사항 활성화**:
   ```hcl
   enable_mfa_requirement = true
   ```

2. **특정 역할만 접근 허용**:
   ```hcl
   allowed_principals = [
     "arn:aws:iam::ACCOUNT-ID:role/WALB-app-github-actions-infra-role"
   ]
   ```

## ⚠️ 주의사항

1. **한 번만 실행**: 이 bootstrap은 프로젝트당 한 번만 실행하면 됩니다.

2. **삭제 방지**: 리소스에 `prevent_destroy = true` 설정되어 있어 실수로 삭제되지 않습니다.

3. **State 파일 보관**: 이 bootstrap의 terraform.tfstate 파일은 **반드시 안전하게 보관**하세요.

4. **권한 필요**: 실행하는 IAM 사용자/역할에 S3, DynamoDB, KMS, CloudTrail 생성 권한이 필요합니다.

## 🔄 업데이트 방법

Bootstrap 리소스 수정이 필요한 경우:

```bash
cd WALB/bootstrap
terraform plan
terraform apply
```

## 🧹 정리 방법

⚠️ **주의**: 이 명령은 모든 Terraform state를 삭제합니다!

```bash
# 삭제 보호 해제 후 (main.tf에서 prevent_destroy = false)
terraform destroy
```

## 📞 문제 해결

### 권한 오류
```
Error: AccessDenied: Access Denied
```
→ IAM 권한 확인 필요

### 버킷 이름 충돌