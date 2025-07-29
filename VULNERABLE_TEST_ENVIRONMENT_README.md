# SK Shieldus 보안 진단 테스트 환경 생성 가이드

## ⚠️ 경고
**이 스크립트는 의도적으로 보안상 취약한 AWS 환경을 생성합니다!**
- 오직 보안 테스트 목적으로만 사용하세요
- 프로덕션 환경에서는 절대 실행하지 마세요
- 테스트 완료 후 반드시 모든 리소스를 삭제하세요

## 📋 개요
SK Shieldus 2024 보안 가이드라인 41개 항목에 대한 취약점을 감지할 수 있는 테스트 환경을 생성합니다.

## 🚀 사용 방법

### 1. AWS CloudShell 접속
```bash
# AWS 콘솔에서 CloudShell 아이콘 클릭 또는
# https://console.aws.amazon.com/cloudshell 접속
```

### 2. 스크립트 다운로드
```bash
# 메인 스크립트
curl -O https://raw.githubusercontent.com/your-repo/create_vulnerable_test_environment.sh
chmod +x create_vulnerable_test_environment.sh

# 추가 취약점 스크립트 (선택사항)
curl -O https://raw.githubusercontent.com/your-repo/create_additional_vulnerabilities.sh
chmod +x create_additional_vulnerabilities.sh
```

### 3. 실행
```bash
# 기본 취약점 환경 생성
./create_vulnerable_test_environment.sh

# 추가 취약점 생성 (선택사항)
./create_additional_vulnerabilities.sh
```

### 4. 진단 테스트
```bash
# SHIELDUS-AWS-CHECKER 실행
python main.py
```

### 5. 정리
```bash
# 자동 생성된 정리 스크립트 실행
./cleanup-vulnerable-resources-[TIMESTAMP].sh
```

## 📊 생성되는 취약점 목록

### 계정 관리 (13개)
- **1.1**: 테스트/관리자 계정 생성
- **1.2**: 단일 사용자에 다중 접근키
- **1.3**: 태그 없는 IAM 사용자
- **1.4**: 그룹 없이 직접 정책 연결
- **1.5**: 키페어 없는 EC2 인스턴스
- **1.6**: S3에 저장된 키페어
- **1.7**: 루트 계정 유사 사용자
- **1.8**: 오래된 접근키 (시뮬레이션)
- **1.9**: MFA 없는 사용자
- **1.10**: 약한 패스워드 정책
- **1.11-1.13**: EKS 관련 (비용상 스킵)

### 권한 관리 (3개)
- **2.1**: EC2에 AdministratorAccess 역할
- **2.2**: 과도한 네트워크 권한 정책
- **2.3**: 와일드카드(*) 권한 정책

### 가상 자원 (10개)
- **3.1**: 0.0.0.0/0 허용 보안그룹
- **3.2**: 불필요한 포트 개방 (Telnet, FTP 등)
- **3.3**: 모든 트래픽 허용 NACL
- **3.4**: 기본 라우트 0.0.0.0/0
- **3.5**: 모든 서브넷에 IGW 연결
- **3.6**: NAT 게이트웨이 (비용상 스킵)
- **3.7**: 퍼블릭 S3 버킷
- **3.8**: 단일 AZ RDS 서브넷
- **3.9-3.10**: EKS/ELB (비용상 스킵)

### 운영 관리 (15개)
- **4.1**: 암호화 안된 EBS 볼륨
- **4.2**: 암호화 안된 RDS (비용상 스킵)
- **4.3**: 암호화 안된 S3 버킷
- **4.4**: HTTP 사용 (HTTPS 미사용)
- **4.5**: 암호화 안된 CloudTrail
- **4.6**: 암호화 안된 CloudWatch 로그
- **4.7**: CloudTrail 비활성화
- **4.8-4.9**: 인스턴스/RDS 로깅 미설정
- **4.10**: S3 버킷 로깅 비활성화
- **4.11**: VPC 플로우 로그 비활성화
- **4.12**: 짧은 로그 보존 기간 (1일)
- **4.13**: 백업 미사용
- **4.14-4.15**: EKS 로깅/암호화 (비용상 스킵)

## 💰 예상 비용
- **최소 비용**: $5-10 (1시간 테스트 기준)
- **주요 비용 요소**:
  - EC2 t2.micro 인스턴스
  - EBS 볼륨
  - S3 스토리지
  - CloudTrail/CloudWatch 로그
  - NAT Gateway (생성 시)

## ⚠️ 주의사항
1. **즉시 삭제**: 테스트 완료 후 즉시 모든 리소스 삭제
2. **비용 모니터링**: AWS Cost Explorer로 비용 확인
3. **권한 제한**: 테스트 계정에서만 실행
4. **알림 설정**: 예상치 못한 활동 감지를 위한 CloudWatch 알람
5. **격리된 환경**: 별도 AWS 계정 사용 권장

## 🛠️ 문제 해결

### 권한 오류
```bash
# 필요한 최소 권한
- IAM: Full access
- EC2: Full access
- S3: Full access
- CloudTrail: Full access
- CloudWatch Logs: Full access
- VPC: Full access
```

### 리소스 생성 실패
```bash
# 리전 확인
aws configure get region

# 서비스 한도 확인
aws service-quotas list-service-quotas --service-code ec2
```

### 정리 스크립트 실패
```bash
# 수동으로 리소스 확인 및 삭제
aws ec2 describe-instances --filters "Name=tag:Name,Values=vulnerable-*"
aws s3 ls | grep vulnerable
aws iam list-users | grep vulnerable
```

## 📚 참고 자료
- [SK Shieldus 클라우드 보안 가이드라인](https://www.skshieldus.com)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [ISMS-P 인증 기준](https://isms.kisa.or.kr)

## 🤝 기여
보안 취약점 테스트 시나리오 개선 제안은 환영합니다!

---
**마지막 업데이트**: 2025-07-29