# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-component AWS security management project with three main components:

1. **SHIELDUS-AWS-CHECKER** - Automated AWS security compliance checker based on SK Shieldus cloud security guidelines
2. **mainHub** - Streamlit-based web UI for integrated security management platform (WALB)
3. **WALB** - Terraform infrastructure-as-code for secure AWS environment provisioning

## Development Environment

**Python Version**: 3.9.0

**Dependencies**: Install from root requirements.txt:

```bash
pip install -r requirements.txt
```

Required packages:

-   streamlit>=1.28.0
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

### mainHub (Streamlit Web UI)

```bash
# Navigate to mainHub directory
cd mainHub

# Run the web application
streamlit run main.py

# Run specific page for development/testing
streamlit run pages/connection.py
streamlit run pages/diagnosis.py
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

### mainHub (WALB Web Platform) Structure

-   **main.py**: Main Streamlit application with account management dashboard
-   **components/**: Reusable UI components and business logic
    -   **session_manager.py**: Manages user sessions and state (공통 모듈)
    -   **aws_handler.py**: AWS service integrations (공통 모듈)
    -   **sk_diagnosis/**: Security diagnosis modules implementing BaseChecker abstract class
    -   **Connection 모듈 (4파일)**: AWS 계정 연결 전용
    -   **Diagnosis 모듈 (5파일)**: 보안 진단 전용
-   **pages/**: Streamlit page modules (connection.py, diagnosis.py)

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

### mainHub Testing

```bash
# Test Streamlit components locally
streamlit run main.py
# Navigate through connection and diagnosis workflows
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

**IMPORTANT**: Only work within the `mainHub/` directory. Other directories (`SHIELDUS-AWS-CHECKER/`, `WALB/`) are managed by team members and should not be modified.

**BACKUP FILES**: Never modify files in the `mainHub/backup/` directory. These are legacy files from before refactoring:
- `backup/connection_backup.py` - Legacy connection page (pre-refactoring)
- `backup/diagnosis_backup.py` - Legacy diagnosis page (pre-refactoring)

These backup files are kept for reference only and should not be used or modified. The current active files are in `mainHub/pages/` and `mainHub/components/`.

### CSS Styling Guidelines

When working with CSS styles in Streamlit applications, **ALWAYS use specific `data-testid` selectors** for better reliability and maintainability:

**Preferred CSS Selectors:**
```css
/* Use data-testid for precise targeting */
div[data-testid="stRadio"] { }
div[data-testid="stSelectbox"] { }
div[data-testid="stButton"] { }
div[data-testid="stExpander"] { }
div[data-testid="stExpanderHeader"] { }
div[data-testid="stExpanderDetails"] { }
div[data-testid="stSidebar"] { }
div[data-testid="stVerticalBlock"] { }
div[data-testid="stHorizontalBlock"] { }
div[data-testid="stColumn"] { }
div[data-testid="metric-container"] { }
```

**Avoid Generic Selectors:**
```css
/* Avoid these - they may break with Streamlit updates */
.streamlit-expanderHeader { } /* Use div[data-testid="stExpanderHeader"] instead */
.stExpander { } /* Use div[data-testid="stExpander"] instead */
.stButton { } /* Use div[data-testid="stButton"] instead */
```

**Best Practices:**
- Always inspect browser DevTools to find the exact `data-testid` values
- Use combination selectors when needed: `div[data-testid="stSidebar"] div[data-testid="stButton"]`
- Add `!important` only when absolutely necessary for Streamlit override
- Test CSS changes across different browsers and Streamlit versions
- Document any custom selectors for future reference

## Project-Specific Notes

-   SHIELDUS-AWS-CHECKER contains 41 security check items based on SK Shieldus guidelines
-   Some checks (EKS-related) require manual verification with kubectl
-   mainHub provides both UI-driven diagnosis and automated infrastructure provisioning
-   Terraform modules are designed for production-ready secure deployments
-   The codebase supports Korean language output for SK Shieldus integration
