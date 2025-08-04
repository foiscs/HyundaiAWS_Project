# WALB - AWS 보안 인프라 자동화 & 통합 모니터링 플랫폼
![Python](https://img.shields.io/badge/Python-3.9.0-blue?style=flat-square&logo=python)
![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple?style=flat-square&logo=terraform)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green?style=flat-square&logo=flask)
![AWS](https://img.shields.io/badge/AWS-Multi_Service-orange?style=flat-square&logo=amazon-aws)

## 📋 프로젝트 개요
**WALB**는 AWS 클라우드 환경에서 보안 컴플라이언스 자동화와 실시간 모니터링을 제공하는 DevSecOps 플랫폼입니다.

### 핵심 목표
- **Infrastructure as Code (IaC)**: Terraform을 활용한 보안 강화 AWS 인프라 자동 구축
- **보안 컴플라이언스 자동화**: SK Shieldus AWS 보안 가이드 기반 41개 항목 자동 진단
- **실시간 보안 모니터링**: Splunk와 연동된 AWS 보안 이벤트 실시간 분석
- **DevSecOps 통합**: 인프라 구축부터 보안 진단까지 통합 워크플로우

### 개발팀
- **팀장**: 박부성
- **팀원**: 고은서, 김선혁, 김태곤, 황태영

---

## 🚀 빠른 시작

### 시스템 요구사항
- **Python**: 3.9.0 (필수)
- **Terraform**: 1.5 이상
- **AWS CLI**: 구성된 AWS 자격 증명
- **Docker**: 컨테이너 환경 (선택적)

### 설치 및 실행

```bash
# 저장소 클론
git clone <repository-url>

# Python 패키지 설치 (루트 디렉토리의 requirements.txt 참조)
pip install -r requirements.txt

# Flask 웹 애플리케이션 실행
cd walb-flask
python run.py
```

Flask 애플리케이션이 http://localhost:5000 에서 실행됩니다.

---

## 🏗️ MSA 아키텍처 구조

### 3-Tier MSA (Microservices Architecture)

```
┌─────────────────────────────────┐
│     🔗 AWS 계정 연결부           │
│   - Cross-Account Role 방식      │  
│   - Access Key 방식             │
│   - 4단계 온보딩 프로세스        │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  🛡️ 41개 보안 자동 진단 & 점검부 │
│   - SK Shieldus 기반 진단       │
│   - 실시간 보안 점검            │  
│   - 자동/수동 조치 실행         │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     📊 Splunk 모니터링부        │
│   - 실시간 로그 수집            │
│   - 보안 이벤트 분석            │
│   - Kinesis 스트리밍 연동       │
└─────────────────────────────────┘
```

### 기술적 연동 구조
```
Terraform(IaC) ──┐
                 ├──▶ AWS Infrastructure ──▶ Security Events ( CloudWatch <== CloudTrail & GuardDuty & SecurityHub ) 
Flask Web UI ────┘                            │
                                              ▼
                                         Kinesis Streams
                                              │
                                              ▼
                                         Splunk Analytics
```

---

## 📂 모듈별 상세 구조

### 1. SHIELDUS-AWS-CHECKER
**SK Shieldus AWS 보안 가이드 기반 CLI 진단 도구**

```
SHIELDUS-AWS-CHECKER/
├── main.py                    # 진단 오케스트레이션 엔진
├── aws_client.py             # AWS 클라이언트 관리 (AWSClientManager)
├── account_management/       # 계정 관리 (13개 체커)
├── authorization/           # 권한 관리 (3개 체커)  
├── virtual_resources/       # 가상 자원 (10개 체커)
└── operation/              # 운영 관리 (15개 체커)
```

**기술 스택**:
- **언어**: Python 3.9.0
- **AWS SDK**: boto3, botocore
- **진단 모듈**: 41개 독립 체커 (동적 로딩)
- **아키텍처**: 모듈화된 체커 시스템, 표준화된 check()/fix() 인터페이스

**주요 기능**:
- SK Shieldus 2024 기준 41개 보안 항목 자동 진단
- 카테고리별 진단: 계정관리(13), 권한관리(3), 가상자원(10), 운영관리(15)
- 자동 조치 및 수동 가이드 제공
- 상세 로깅 및 결과 리포트

### 2. walb-flask
**Flask 기반 웹 UI 통합 보안 관리 플랫폼**

```
walb-flask/
├── app/
│   ├── checkers/            # SHIELDUS 체커 Flask 이식 (41개)
│   │   ├── base_checker.py  # BaseChecker 추상 클래스
│   │   ├── account_management/  (13개 구현 완료)
│   │   ├── authorization/       (3개 구현 완료)
│   │   ├── virtual_resources/   (10개 구현 완료)
│   │   └── operation/          (15개 구현 완료)
│   ├── services/           # 비즈니스 로직
│   │   ├── diagnosis_service.py    # 진단 엔진
│   │   ├── monitoring_service.py   # 모니터링 서비스
│   │   ├── kinesis_service.py      # Kinesis 연동
│   │   └── splunk_service.py       # Splunk 연동
│   ├── views/              # Flask 블루프린트
│   └── config/             # 설정 관리
├── templates/              # Jinja2 HTML 템플릿
├── static/                # CSS/JavaScript 정적 파일
└── data/                  # JSON 데이터 저장소
```

**기술 스택**:
- **Backend**: Flask 2.3.3, Python 3.9.0
- **Frontend**: Tailwind CSS, Vanilla JavaScript, Jinja2 템플릿
- **AWS 연동**: boto3, Cross-Account Role/Access Key 지원
- **데이터**: JSON 파일 기반 계정/진단 이력 관리
- **아키텍처**: Blueprint 기반 모듈화, MVC 패턴

**주요 기능**:
- **4단계 AWS 계정 온보딩**: 방식선택 → 권한설정 → 정보입력 → 연결테스트
- **실시간 보안 진단**: 41개 항목 개별/일괄 진단, 실시간 진행률 표시
- **자동/수동 조치**: 웹 UI 기반 보안 조치 실행 및 가이드
- **다중 계정 관리**: Cross-Account Role 및 Access Key 방식 지원
- **모니터링 대시보드**: Splunk 연동 실시간 보안 이벤트 모니터링

### 3. WALB (Terraform Infrastructure)
**보안 강화 AWS 인프라 자동 구축**

```
WALB/
├── infrastructure/
│   ├── walb_terraform/        # 메인 보안 인프라
│   ├── helm-lbc/             # AWS Load Balancer Controller
│   └── test_tf/              # 테스트 환경
├── bootstrap/                # 초기 부트스트랩 설정  
├── server1/                  # PHP 웹 애플리케이션
└── scripts/                  # Splunk 연동 스크립트
```

**walb_terraform 보안 모듈 (13개)**:
```
modules/
├── aws-config/              # AWS Config 컴플라이언스 규칙
├── cloudtrail/              # API 호출 감사 로깅
├── dnsresolve/              # DNS 보안 설정
├── dynamodb/                # DynamoDB 보안 설정
├── ecr/                     # Container Registry 보안
├── eks/                     # EKS 클러스터 보안
├── guardduty/               # 위협 탐지 및 분석
├── iam-security/            # IAM 정책 보안 검증
├── rds/                     # RDS 데이터베이스 보안
├── s3/                      # S3 스토리지 보안
├── securityhub/             # Security Hub 중앙 관리
├── vpc/                     # VPC 네트워크 보안
└── vpcflow/                 # VPC Flow Logs 모니터링
```

**기술 스택**:
- **IaC**: Terraform, 13개 보안 모듈 구성
- **AWS 보안 서비스**: Config, CloudTrail, GuardDuty, Security Hub, WAF, VPC Flow Logs
- **컨테이너**: EKS + ECR + Helm Load Balancer Controller
- **애플리케이션**: PHP 웹앱 + MySQL RDS + DynamoDB
- **모니터링**: Splunk 연동 실시간 로그 포워딩

**주요 기능**:
- **13개 보안 모듈**: 각 AWS 서비스별 전용 보안 설정
- **멀티 환경 지원**: walb_terraform(운영) + test_tf(테스트)
- **컴플라이언스 자동화**: AWS Config + Security Hub 통합
- **실시간 위협 탐지**: GuardDuty + VPC Flow Logs 연동

### 4. kinesis_splunk_forwarder.py
**AWS Kinesis → Splunk 실시간 로그 포워딩**

**기술 스택**:
- **언어**: Python 3.9.0
- **AWS SDK**: boto3 (Kinesis, STS)
- **로그 처리**: gzip 압축 해제, JSON 파싱
- **멀티스레딩**: ThreadPoolExecutor 기반 병렬 처리

**주요 기능**:
- **3개 스트림 지원**: CloudTrail, GuardDuty, Security Hub
- **실시간 데이터 처리**: Kinesis Shard 기반 스트리밍
- **로그 포매팅**: Splunk 호환 JSON 로그 생성
- **인증 방식**: Cross-Account Role/Access Key 지원

### 5. BlogServer
**PHP 기반 블로그 애플리케이션 (테스트용)**

```
BlogServer/
├── files/app/              # PHP 애플리케이션
├── k8s/                   # Kubernetes 매니페스트
├── Dockerfile             # 컨테이너화
└── composer.json          # PHP 의존성
```

**기술 스택**:
- **언어**: PHP, MySQL
- **컨테이너**: Docker, Kubernetes
- **CI/CD**: GitHub Actions 연동
- **스토리지**: AWS S3 연동

---

## 🔧 핵심 기술 스택

### 🚀 핵심 프레임워크
- **🏗️ Terraform**: Infrastructure as Code - 보안 강화 AWS 인프라 자동 구축의 핵심
- **📊 Splunk**: 실시간 보안 모니터링 - AWS 보안 이벤트 통합 분석 플랫폼

### Backend
- **Python 3.9.0**: 메인 개발 언어
- **Flask 2.3.3**: 웹 프레임워크
- **boto3 1.34.0**: AWS SDK

### Frontend  
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **Vanilla JavaScript**: 경량 클라이언트 사이드 로직
- **Jinja2**: Flask 템플릿 엔진

### AWS Services
- **Core**: EC2, VPC, IAM, S3
- **Container**: EKS, ECR, Docker
- **Database**: RDS (MySQL/PostgreSQL)
- **Security**: CloudTrail, GuardDuty, Security Hub, WAF
- **Monitoring**: CloudWatch, Kinesis Data Streams
- **Storage**: S3, EBS

### DevOps
- **CI/CD**: GitHub Actions
- **Container**: Docker, Kubernetes, Helm
- **Security**: TFSec, SK Shieldus 가이드

---

## 🔒 보안 기능

### SK Shieldus 기반 41개 진단 항목
- **계정 관리 (13개)**: IAM 사용자, MFA, 패스워드 정책, EKS 권한
- **권한 관리 (3개)**: 서비스 정책, 네트워크 정책, 과도한 권한
- **가상 자원 (10개)**: 보안 그룹, ACL, 라우팅, S3 접근 제어
- **운영 관리 (15개)**: 암호화, 로깅, 백업, 모니터링

### 자동화된 보안 조치
- **자동 조치**: 위험 요소 즉시 수정
- **수동 가이드**: 복잡한 설정에 대한 단계별 가이드
- **실시간 알림**: Splunk 연동 보안 이벤트 알림

---

## 📊 워크플로우

### 1. 인프라 구축 단계

#### 0단계: Bootstrap (S3 백엔드 생성)
```bash
cd WALB/bootstrap
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
# Terraform 상태 파일용 S3 버킷 및 DynamoDB 테이블 생성
```

#### 1단계: 메인 인프라 (13개 보안 모듈)
```bash
cd WALB/infrastructure/walb_terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
# VPC, EKS, RDS, S3, 보안 서비스들 일괄 배포
```

#### 2단계: AWS Load Balancer Controller
```bash
cd WALB/infrastructure/helm-lbc
chmod +x generate-tfvars.sh
./generate-tfvars.sh           # 1단계 결과에서 자동으로 설정값 추출
terraform init
terraform plan
terraform apply
# EKS 클러스터에 ALB Controller 배포
```

#### 3단계: 애플리케이션 배포 (GitHub Actions)
```bash
# WALB/server1 폴더 변경 시 자동 트리거
git add WALB/server1/
git commit -m "Update PHP application"
git push origin main
# GitHub Actions 워크플로우가 자동으로:
# - PHP 애플리케이션 빌드 및 ECR 푸시
# - EKS 클러스터에 배포
# - 헬스체크 및 롤백 처리
```

### 2. 보안 진단 단계  
```bash
# CLI 방식
cd SHIELDUS-AWS-CHECKER
python main.py

# 웹 UI 방식
cd walb-flask
python run.py
# http://localhost:5000 접속
```

### 3. 모니터링 단계
```bash
# Kinesis → Splunk 포워딩 시작
python kinesis_splunk_forwarder.py
```

---

<div align="center">

**🛡️ WALB로 더 안전한 AWS 클라우드 환경을 구축하세요 🛡️**

</div>
