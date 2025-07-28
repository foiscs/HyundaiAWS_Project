# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**언어 설정**: 앞으로 모든 질의응답은 한글로 수행합니다.

## Project Overview

This is a multi-component AWS security management project with three main components:

1. **SHIELDUS-AWS-CHECKER** - Automated AWS security compliance checker based on SK Shieldus cloud security guidelines
2. **walb-flask** - Flask 기반 웹 UI로 통합 보안 관리 플랫폼 (WALB) - mainHub에서 이식 완료
3. **WALB** - Terraform infrastructure-as-code for secure AWS environment provisioning

## Development Environment

**Python Version**: 3.9.0

**Dependencies**:

### walb-flask 요구사항:

```bash
cd walb-flask
pip install -r requirements.txt
```

주요 패키지:

-   Flask>=2.3.0
-   boto3>=1.20.0
-   botocore>=1.23.0
-   python-dateutil>=2.8.2

## Common Development Commands

### SHIELDUS-AWS-CHECKER (Security Scanner)

```bash
# Navigate to checker directory
cd SHIELDUS-AWS-CHECKER

# Run full security check (requires AWS credentials)
python main.py

# Check specific module
python -c "from account_management.1_1_user_account import check; check()"
```

### walb-flask (Flask Web UI)

```bash
# Navigate to walb-flask directory
cd walb-flask

# Run the Flask application
python run.py

# Or using Flask CLI
flask run --host=0.0.0.0 --port=5000
```

### WALB (Terraform Infrastructure)

```bash
# Navigate to terraform directory
cd WALB/infrastructure/terraform

# Initialize terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure (requires AWS credentials and terraform.tfvars)
terraform apply
```

## Code Architecture

### SHIELDUS-AWS-CHECKER Structure

-   **main.py**: Orchestrates all security checks, loads modules dynamically from CHECK_MODULES dictionary
-   **aws_client.py**: Centralized AWS client management with AWSClientManager, AWSServiceChecker, and AWSResourceCounter classes
-   **account_management/**: IAM and user account security checks (13 modules)
-   **authorization/**: Service policy and permission checks (3 modules)
-   **virtual_resources/**: Network and infrastructure security checks (10 modules)
-   **operation/**: Encryption, logging, and operational security checks (15 modules)

Each security check module must implement:

-   `check()` function that returns findings (truthy values indicate vulnerabilities)
-   Optional `fix()` function for automated remediation

### walb-flask (Flask Web Platform) Structure

-   **app/**init**.py**: Flask 애플리케이션 팩토리
-   **app/models/**: 데이터 모델 (account.py - AWS 계정 관리)
-   **app/services/**: 비즈니스 로직 (diagnosis_service.py - 진단 엔진)
-   **app/views/**: Flask 블루프린트 라우트 (main, connection, diagnosis, api)
-   **app/checkers/**: 보안 진단 체커 모듈
    -   **base_checker.py**: BaseChecker 추상 클래스
    -   **account_management/**: 계정 관리 체커 (1.1-1.13)
    -   **authorization/**: 권한 관리 체커 (2.1-2.3)
-   **templates/**: Jinja2 HTML 템플릿
-   **static/**: 정적 파일 (CSS, JavaScript)

#### Diagnosis System Architecture (진단 시스템 구조) - 5파일 구조

진단 시스템은 5개 파일로 모듈화되어 각 파일이 명확한 역할을 담당합니다:

**Core Architecture Pattern:**

```
diagnosis.py (Entry Point)
    ↓
DiagnosisUI (Unified Interface)
    ↓
DiagnosisCoreEngine (Business Logic)
```

**주요 모듈별 역할:**

1. **pages/diagnosis.py** (메인 진입점 - 80줄)

    - SK Shieldus 41개 항목 보안 진단 페이지 메인 진입점
    - DiagnosisUI 인스턴스 생성 및 단계별 렌더링 오케스트레이션
    - 계정 선택 확인, CSS/HTML 로딩, 사이드바/메인 컨텐츠 렌더링

2. **diagnosis_ui.py** (통합 UI - 520줄)

    - **DiagnosisUI**: 모든 UI 기능을 통합한 단일 클래스 (페이지+컴포넌트+핸들러)
    - 페이지 렌더링: 사이드바, 레이아웃 제어, 진단 항목, 통계 정보
    - 컴포넌트 렌더링: 카테고리별 항목, 개별 진단 카드, 계정 정보 카드
    - 핸들러 기능: 진단/조치 실행(엔진 위임), 재진단 버튼, 환경 검증

3. **diagnosis_engine.py** (비즈니스 로직 - 170줄)
    - **DiagnosisCoreEngine**: AWS 보안 진단의 핵심 비즈니스 로직
    - UI와 완전 분리된 순수 진단 실행 엔진
    - 주요 기능:
        - AWS 세션 생성 (Role ARN/Access Key 방식)
        - 진단 항목 실행 및 결과 반환
        - 자동 조치 실행 (그룹 할당 포함)
        - 진단 환경 검증
        - AWS 세션 연결 테스트 (UI 전용)
4. **diagnosis_config.py** (데이터 관리 - 115줄)

    - SK Shieldus 41개 보안 진단 항목 정의
    - 중요도/위험도별 색상 매핑 상수
    - **DiagnosisDataConfig**: 진단 설정 클래스

5. **diagnosis_templates.py** (HTML 템플릿 - 96줄)

    - CSS와 완전 분리된 순수 HTML 템플릿
    - 히어로 헤더, 로딩 템플릿, 계정 카드, 위험도 배지
    - 자동 스크롤 스크립트 (특정 컴테이너 및 진단 완료용)

6. **diagnosis_styles.py** (CSS 스타일 - 327줄)
    - 모든 진단 관련 CSS 스타일 중앙 집중 관리
    - 히어로 헤더, 진단 카드, 진행 상태, 결과 표시, 레이아웃 스타일
    - 공통 스타일(connection_styles)과 진단 전용 스타일 통합

**진단 시스템 주요 특징:**

-   **완전한 관심사 분리**: 5개 파일로 역할별 명확한 분리 (UI/비즈니스/데이터/템플릿/스타일)
-   **진단 항목 관리**: SK Shieldus 기준 41개 항목 (계정관리 13개, 권한관리 3개, 가상리소스 10개, 운영관리 15개)
-   **실시간 진단**: 개별 항목 또는 전체 일괄 진단 지원
-   **위험도 기반 분류**: 상(13개), 중(25개), 하(3개) 위험도별 분류
-   **반응형 UI**: 1열/2열 레이아웃, 실시간 진행률 표시, 자동 스크롤
-   **자동 조치**: 진단 결과에 따른 자동 조치 실행 (체커별 구현)
-   **AWS 세션 관리**: Role ARN/Access Key 두 방식 지원, 세션 테스트 기능

**진단 흐름:**

```
1. 계정 선택 → 2. 진단 항목 선택 → 3. AWS 세션 생성 → 4. 체커 실행 → 5. 결과 표시 → 6. 조치 실행 (선택적)
```

**기술적 패턴:**

-   **BaseChecker 추상 클래스**: `components/sk_diagnosis/base_checker.py`에서 모든 진단 모듈 인터페이스 정의
-   **계정 데이터 저장**: `registered_accounts.json`에 한 줄당 하나의 JSON 객체로 저장
-   **Streamlit 세션 상태**: 내비게이션 및 데이터 지속성에 활용
-   **5파일 모듈 아키텍처**: 유지보수성과 명확성을 위한 완전한 관심사 분리
-   **체커별 UI 위임**: 각 진단 체커가 자체 `render_result_ui()`, `render_fix_form()` 메서드 구현

#### Connection System Architecture (연결 시스템 구조) - 4파일 구조

AWS 계정 연결 시스템은 4개 파일로 모듈화되어 각 파일이 명확한 역할을 담당합니다:

**Core Architecture Pattern:**

```
connection.py (Entry Point)
    ↓
ConnectionUI (Unified Interface)
    ↓
ConnectionEngine (Business Logic) → AWSConnectionHandler (공통 모듈)
```

**주요 모듈별 역할:**

1. **pages/connection.py** (메인 진입점 - 69줄)

    - AWS 계정 연결 4단계 온보딩 프로세스의 간단한 컨트롤러
    - ConnectionUI 인스턴스 생성 및 단계별 렌더링 오케스트레이션
    - 세션 초기화, CSS 적용, 사이드바 렌더링

2. **connection_ui.py** (통합 UI - 800줄)

    - **ConnectionUI**: 모든 Connection UI 기능을 담당하는 통합 클래스 (페이지+컴포넌트)
    - 페이지 렌더링: 4단계별 온보딩 프로세스 (방식선택 → 권한설정 → 정보입력 → 연결테스트)
    - 컴포넌트 렌더링: 단계표시기, 연결방식 카드, 정보박스, JSON 코드블록, 테스트 결과
    - 유틸리티 기능: 실시간 검증, 세션 업데이트, 민감정보 정리

3. **connection_engine.py** (비즈니스 로직 - 350줄)

    - **ConnectionEngine**: Connection 전용 비즈니스 로직 엔진
    - UI와 완전 분리된 순수 비즈니스 로직
    - 주요 기능:
        - AWS 연결 테스트 실행 (Cross-Account Role/Access Key 방식)
        - 계정 등록 처리 및 폼 검증
        - IAM 정책 생성 (Trust/Permission Policy)
        - 입력값 검증 및 계정 데이터 추출
        - aws_handler 모듈 활용으로 중복 코드 제거

4. **connection_config.py** (데이터 관리 - 280줄)

    - 모든 Connection 관련 상수, 기본값, 설정을 중앙 집중 관리
    - **ConnectionConfig**: 설정 관리 클래스
    - 4단계 정의, 연결 방식 정보, AWS 리전 목록, 검증 규칙
    - 기본 세션 상태, 정보 박스 타입, WALB 서비스 정보

5. **connection_templates.py** (HTML 템플릿 - 350줄)

    - CSS와 완전 분리된 순수 HTML 템플릿
    - 히어로 헤더, 단계 표시기, 연결방식 카드, 정보박스
    - JSON 코드 블록, 테스트 결과 테이블, 로딩 스피너, 네비게이션 버튼

6. **connection_styles.py** (CSS 스타일 - 312줄)
    - 모든 Connection 관련 CSS 스타일 중앙 집중 관리
    - 폰트, 버튼, expander, 메인 페이지 스타일
    - diagnosis와 공통 스타일 함수 제공 (inject_custom_font, inject_custom_button_style 등)

**Connection 시스템 주요 특징:**

-   **완전한 관심사 분리**: 4개 파일로 UI/비즈니스/데이터/템플릿 완전 분리
-   **4단계 온보딩**: 방식선택 → 권한설정 → 정보입력 → 연결테스트
-   **2가지 연결 방식**: Cross-Account Role (권장) / Access Key 방식 지원
-   **실시간 검증**: 입력값 실시간 검증 및 오류 표시
-   **IAM 정책 자동 생성**: Trust Policy/Permission Policy 자동 생성 및 표시
-   **반응형 UI**: 단계별 진행 표시, 동적 폼 검증, 테스트 결과 시각화
-   **보안 강화**: 민감정보 자동 정리, 마스킹된 입력, 세션 관리

**기술적 패턴:**

-   **공통 모듈 활용**: aws_handler.py, session_manager.py 재사용으로 코드 중복 제거
-   **계정 데이터 저장**: `registered_accounts.json`에 한 줄당 하나의 JSON 객체로 저장
-   **Streamlit 세션 상태**: 4단계 진행 상태 및 폼 데이터 지속성 관리
-   **4파일 모듈 아키텍처**: 유지보수성과 확장성을 위한 완전한 관심사 분리
-   **템플릿 기반 렌더링**: HTML 템플릿과 CSS 완전 분리로 디자인 일관성 확보

### WALB Terraform Structure

-   **main.tf**: Complete AWS infrastructure orchestration
-   **modules/**: Modular infrastructure components (vpc, eks, rds, s3, dynamodb, ecr)
-   **terraform.tfvars**: Environment-specific variable values
-   **security.tf**: Centralized security configurations
-   Follows security-first design with encryption, logging, and access controls built-in

## AWS Authentication

All components require valid AWS credentials. Configure via one of:

-   AWS CLI: `aws configure`
-   Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
-   IAM roles (when running on EC2/EKS)
-   AWS profiles: Set profile name in connection configuration

## Testing and Validation

No automated test framework is currently configured. Manual testing approaches:

### SHIELDUS-AWS-CHECKER Testing

```bash
# Test individual security check modules
python -c "from operation.4_1_ebs_encryption import check; print(check())"

# Verify AWS client connectivity
python -c "from aws_client import AWSClientManager; mgr = AWSClientManager(); print(mgr.validate_credentials())"
```

### walb-flask Testing

```bash
# Flask 애플리케이션 테스트
cd walb-flask
python run.py
# 브라우저에서 http://localhost:5000 접속하여 연결 및 진단 워크플로우 테스트
```

### WALB Testing

```bash
# Validate Terraform configuration
terraform validate

# Plan without applying changes
terraform plan -var-file="terraform.tfvars"
```

## Security Considerations

-   Never commit AWS credentials, access keys, or sensitive data
-   Use IAM roles and policies with minimal required permissions
-   All Terraform modules include encryption by default
-   Log outputs are sanitized to prevent credential exposure
-   WALB follows ISMS-P compliance patterns

## Development Guidelines

**IMPORTANT**: 주로 `walb-flask/` 디렉토리에서 작업합니다. `SHIELDUS-AWS-CHECKER/`와 `WALB/` 디렉토리는 팀원들이 관리하므로 수정하지 마세요.

**참고사항**: `mainHub/` 디렉토리는 레거시 Streamlit 기반 코드로, 현재는 `walb-flask/`로 완전히 이식되었습니다.

### Flask 개발 가이드라인

**체커 구현 규칙:**

-   모든 체커는 `BaseChecker` 클래스를 상속받아야 합니다
-   `run_diagnosis()`, `execute_fix()` 메서드를 필수로 구현해야 합니다
-   CLI 입력 대신 웹 인터페이스에서 사용자 상호작용을 처리해야 합니다
-   `print()` 문 대신 구조화된 데이터를 반환해야 합니다

**CSS 스타일링 가이드라인:**

-   Tailwind CSS 클래스를 우선적으로 사용합니다
-   커스텀 CSS는 `static/css/` 디렉토리에 모듈별로 분리합니다
-   반응형 디자인을 고려하여 모바일/데스크톱 호환성을 유지합니다

**JavaScript 가이드라인:**

-   바닐라 JavaScript를 사용하며 jQuery 등 외부 라이브러리는 피합니다
-   AJAX 요청은 fetch API를 사용합니다
-   에러 처리와 로딩 상태 표시를 필수로 구현합니다

## Project-Specific Notes

-   SHIELDUS-AWS-CHECKER contains 41 security check items based on SK Shieldus guidelines
-   Some checks (EKS-related) require manual verification with kubectl
-   walb-flask provides web-based UI for diagnosis and AWS account management
-   Terraform modules are designed for production-ready secure deployments
-   The codebase supports Korean language output for SK Shieldus integration
-   현재 16개 체커만 Flask용으로 구현되어 있으며, 나머지 25개는 추가 구현이 필요합니다

## Flask 보안 진단 체커 구현 지시사항

### 핵심 구현 원칙

**CRITICAL**: 원본 SHIELDUS-AWS-CHECKER의 팀원 구현을 **정확히** 복사해야 합니다.

-   모든 print 메시지를 그대로 보존
-   수동 조치 가이드를 완전히 보존
-   자동화 불가능성 경고를 그대로 유지
-   과도한 엔지니어링이나 기능 추가 금지

### 체커 구현 패턴

1. **BaseChecker 상속**: 모든 체커는 `app.checkers.base_checker.BaseChecker` 상속
2. **필수 메서드 구현**:

    - `run_diagnosis()`: 원본 `check()` 함수 로직 그대로 구현
    - `execute_fix()`: 원본 `fix()` 함수 로직 그대로 구현
    - `_get_manual_guide()`: 수동 조치가 필요한 경우 웹 UI용 가이드 제공

3. **수동 조치 가이드 시스템**:
    - 원본에서 수동 조치가 필요한 경우 `_get_manual_guide()` 메서드 구현
    - 단계별 가이드를 웹 UI에서 표시 가능한 형태로 변환
    - 원본의 모든 경고 메시지와 절차를 보존

### 구현된 체커 현황 (16개)

**계정 관리 (13개 완료)**:

-   1.1-1.10: 기본 계정 관리 체커들 (자동 조치 + 수동 가이드)
-   1.11-1.13: EKS 관련 체커들 (VPC 내부 접근 필요하여 수동 전용)

**권한 관리 (3개 완료)**:

-   2.1-2.3: 서비스 정책 체커들 (위험성으로 인해 수동 전용)

### 수동 조치 가이드 구현 사례

#### 1. EKS 체커 (1.11-1.13)

-   **문제**: Kubernetes API 접근을 위해 VPC 내부 접근 필요
-   **해결**: kubectl 명령어와 단계별 가이드 제공
-   **구현**: `_get_manual_guide()`에서 VPC 접속 → kubectl 설정 → 점검 → 조치 단계 안내

#### 2. 정책 관리 체커 (2.1-2.3)

-   **문제**: 권한 정책 변경이 운영에 큰 영향을 줄 수 있음
-   **해결**: 수동 점검 및 신중한 조치 가이드 제공
-   **구현**: 원본의 경고 메시지를 웹 UI 경고 박스로 변환

#### 3. Key Pair 관리 (1.5)

-   **문제**: 실행 중인 인스턴스에 Key Pair 추가는 재시작 필요
-   **해결**: 두 가지 방법 제시 (authorized_keys 수정 / AMI 재생성)
-   **구현**: 원본의 "방법\_1", "방법\_2" 가이드를 단계별로 웹 UI에 표시

```python
# 원본 1.5 체커의 수동 조치 메시지 예시
print("  └─ 방법_1. [Authorize_keys 직접 수정]: 실행 중인 인스턴스에 SSH로 접속하여 ~/.ssh/authorized_keys 파일에 새 key pair의 public key를 수동으로 추가")
print("  └─ 방법_2. [AMI로 새 인스턴스 생성]: 기존 인스턴스에서 AMI 이미지를 만들어 새로운 인스턴스를 생성할 때 새 key pair를 지정")
```

### 수동 가이드 웹 UI 표시 형태

```javascript
manual_guide: {
    title: '진단 항목 수동 조치 가이드',
    description: '원본 팀원이 작성한 수동 절차를 따라 보안을 강화하세요.',
    steps: [
        {
            type: 'warning',  // warning, info, step, commands, danger
            title: '[FIX] 조치 제목',
            content: '조치 설명'
        },
        {
            type: 'step',
            title: '1. 첫 번째 단계',
            content: '단계별 설명'
        },
        {
            type: 'commands',
            title: 'CLI 명령어',
            content: ['command1', 'command2']  // 복사 가능한 명령어 배열
        }
    ]
}
```

### UX 개선사항

1. **실시간 진행 상황**: 전체 진단 시 왼쪽 사이드바에 실시간 진행률, 완료/실패 통계, 색상 코딩된 로그 표시
2. **스크롤 자동 이동**: 현재 진단 중인 항목으로 자동 스크롤 + 시각적 강조 효과
3. **결과 유지**: 진단 완료 후 사이드바 결과를 페이지 새로고침/이동 전까지 유지
4. **명령어 복사**: 수동 가이드의 CLI 명령어에 원클릭 복사 버튼 제공

### 구현 우선순위

**다음 구현 대상 (25개 남음)**:

1. **가상 자원 (3.1-3.10)**: 보안 그룹, VPC, 네트워크 설정 체커
2. **운영 관리 (4.1-4.15)**: 암호화, 로깅, 모니터링 체커

**구현 시 주의사항**:

-   원본 체커의 모든 로직과 메시지를 정확히 보존
-   자동 조치가 위험한 경우 반드시 수동 가이드로 구현
-   웹 UI에서 사용자 상호작용이 필요한 부분은 적절히 변환
-   모든 체커를 `diagnosis_service.py`의 `checker_mapping`에 등록
