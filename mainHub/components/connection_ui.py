"""
WALB Connection UI 렌더링 모듈
모든 Connection 관련 UI 기능을 통합한 단일 클래스

Classes:
- ConnectionUI: 모든 Connection UI 기능을 담당하는 통합 클래스

Page Methods (페이지 렌더링):
- render_header: 메인 헤더 렌더링 (그라데이션 히어로 섹션)
- render_step1: 1단계 - 연결 방식 선택 (Cross-Account Role vs Access Key)
- render_step2: 2단계 - 권한 설정 가이드 (IAM 정책 표시)
- render_step3: 3단계 - 연결 정보 입력 (폼 검증 포함)
- render_step4: 4단계 - 연결 테스트 및 결과 표시
- render_sidebar: 사이드바 패널 (디버깅 정보)

Component Methods (컴포넌트 렌더링):
- step_indicator: 4단계 진행 표시기
- connection_type_card: 연결방식 선택 카드
- info_box: 정보/경고 박스 (4가지 타입)
- json_code_block: JSON 정책 코드 블록
- test_result_table: 연결 테스트 결과 테이블
- loading_spinner: 로딩 스피너
- input_field_with_toggle: 비밀번호 토글 입력필드
- navigation_buttons: 네비게이션 버튼

Utility Methods (유틸리티):
- validate_and_show_error: 실시간 입력 검증
- safe_session_update: 안전한 세션 업데이트
- get_actual_secret_key: 마스킹된 Secret Key 실제값 반환
- cleanup_sensitive_data: 민감정보 자동 정리
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from components.connection_engine import ConnectionEngine
from components.connection_config import ConnectionConfig, get_step_definitions, get_connection_types, get_available_regions
from components.connection_templates import (
    get_hero_header_template, get_step_indicator_template, get_connection_type_card_template,
    get_info_box_template, get_json_code_block_template, get_test_result_table_template,
    get_loading_spinner_template, get_navigation_buttons_template
)

class ConnectionUI:
    """Connection UI 통합 클래스 - 모든 UI 렌더링과 컴포넌트 기능을 하나로 통합"""
    
    def __init__(self):
        """UI 클래스 초기화"""
        self.engine = ConnectionEngine()
        self.config = ConnectionConfig()
    
    # ================================
    # 페이지 렌더링 (기존 connection.py)
    # ================================
    
    def render_header(self) -> None:
        """페이지 헤더 렌더링 - 히어로 섹션과 단계 표시기"""
        # 히어로 헤더
        header_html = get_hero_header_template()
        components.html(header_html, height=180)
        
        # 단계 표시기 (세션 상태 안전 확인)
        current_step = st.session_state.get('current_step', 1)
        self.step_indicator(current_step)
    
    def render_step1(self) -> None:
        """1단계: 연결 방식 선택 렌더링"""
        st.markdown("### 🔗 AWS 연결 방식을 선택해주세요")
        st.markdown("보안 수준과 설정 복잡도를 고려하여 적절한 연결 방식을 선택하세요.")
        
        col1, col2 = st.columns(2)
        connection_types = get_connection_types()
        
        with col1:
            role_info = connection_types["cross-account-role"]
            if st.button("🛡️ Cross-Account Role 선택", key="select_role", use_container_width=True):
                st.session_state.connection_type = "cross-account-role"
                self.safe_session_update('current_step', 2)
            
            self.connection_type_card(
                title=role_info["title"],
                subtitle=role_info["subtitle"], 
                description=role_info["description"],
                pros="• 높은 보안성\n• 임시 자격 증명 사용\n• 세밀한 권한 제어",
                is_selected=st.session_state.connection_type == "cross-account-role",
                icon=role_info["icon"],
                card_type="role"
            )
        
        with col2:
            key_info = connection_types["access-key"]
            if st.button("🔑 Access Key 선택", key="select_key", use_container_width=True):
                st.session_state.connection_type = "access-key"
                self.safe_session_update('current_step', 2)
            
            self.connection_type_card(
                title=key_info["title"],
                subtitle=key_info["subtitle"],
                description=key_info["description"], 
                pros="• 간단한 설정\n• 빠른 연결\n• 즉시 사용 가능",
                is_selected=st.session_state.connection_type == "access-key",
                icon=key_info["icon"],
                card_type="key"
            )
        
        # 정보 박스
        if st.session_state.connection_type == "cross-account-role":
            self.info_box(
                "Cross-Account Role은 AWS에서 권장하는 가장 안전한 연결 방식입니다. "
                "임시 자격 증명을 사용하여 장기 키 노출 위험을 최소화합니다.",
                "info",
                "권장 연결 방식"
            )
        elif st.session_state.connection_type == "access-key":
            self.info_box(
                "Access Key 방식은 설정이 간단하지만 장기 자격 증명을 사용합니다. "
                "정기적인 키 로테이션과 최소 권한 원칙을 준수해주세요.",
                "warning",
                "보안 주의사항"
            )
    
    def render_step2(self) -> None:
        """2단계: 권한 설정 가이드 렌더링"""
        connection_type = st.session_state.connection_type
        
        if connection_type == "cross-account-role":
            self._render_step2_role()
        elif connection_type == "access-key":
            self._render_step2_access_key()
        
        # 네비게이션
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← 이전 단계", key="step2_prev"):
                self.safe_session_update('current_step', 1)
        with col2:
            if st.button("다음 단계 →", key="step2_next", type="primary"):
                self.safe_session_update('current_step', 3)
    
    def _render_step2_role(self) -> None:
        """2단계: Cross-Account Role 설정 가이드"""
        st.markdown("### 🛡️ Cross-Account Role 설정")
        
        # External ID 생성
        if st.button("🎲 External ID 생성", key="generate_external_id"):
            external_id = self.engine.generate_external_id()
            st.session_state.account_data['external_id'] = external_id
            st.success(f"External ID가 생성되었습니다: `{external_id}`")
        
        # External ID 표시
        if st.session_state.account_data.get('external_id'):
            st.markdown(f"**생성된 External ID:** `{st.session_state.account_data['external_id']}`")
        
        # Trust Policy
        external_id = st.session_state.account_data.get('external_id', 'walb-example-id')
        trust_policy = self.engine.generate_trust_policy(external_id)
        
        st.markdown("#### 1️⃣ IAM Role Trust Relationship 설정")
        self.info_box(
            "AWS Console에서 새 IAM Role을 생성하고 아래 Trust Policy를 설정하세요.",
            "info",
            "Trust Policy 설정"
        )
        
        self.json_code_block(trust_policy, "Trust Relationship Policy")
        
        # Permission Policy
        st.markdown("#### 2️⃣ IAM Role Permission 설정")
        permission_policy = self.engine.generate_permission_policy()
        
        self.info_box(
            "생성한 Role에 아래 Permission Policy를 연결하세요. "
            "이 정책은 보안 진단에 필요한 최소 권한만 포함합니다.",
            "info",
            "Permission Policy 설정"
        )
        
        self.json_code_block(permission_policy, "WALB Security Diagnosis Policy")
        
        # 설정 단계 안내
        st.markdown("#### 📋 설정 단계")
        steps_text = """
        1. AWS Console → IAM → Roles → Create role
        2. Trusted entity type: AWS account 선택
        3. Account ID: `{}` 입력
        4. Require external ID 체크 후 생성된 External ID 입력
        5. Permission policies: 위의 JSON 정책을 Custom policy로 생성 후 연결
        6. Role name 설정 (예: WALBSecurityDiagnosisRole)
        7. Role ARN 복사하여 다음 단계에서 입력
        """.format(self.engine.get_walb_service_account_id())
        
        self.info_box(steps_text, "info", "IAM Role 생성 단계")
    
    def _render_step2_access_key(self) -> None:
        """2단계: Access Key 설정 가이드"""
        st.markdown("### 🔑 Access Key 설정")
        
        # Permission Policy
        permission_policy = self.engine.generate_permission_policy()
        
        st.markdown("#### 1️⃣ IAM User 생성 및 정책 연결")
        self.info_box(
            "AWS Console에서 새 IAM User를 생성하고 아래 정책을 연결하세요. "
            "이 정책은 보안 진단에 필요한 최소 권한만 포함합니다.",
            "info",
            "IAM User 설정"
        )
        
        self.json_code_block(permission_policy, "WALB Security Diagnosis Policy")
        
        st.markdown("#### 2️⃣ Access Key 생성")
        
        steps_text = """
        1. AWS Console → IAM → Users → Create user
        2. User name 설정 (예: walb-security-diagnosis)
        3. Attach policies directly 선택
        4. Create policy → JSON 탭에서 위 정책 내용 붙여넣기
        5. 정책 이름 설정 후 생성 (예: WALBSecurityDiagnosisPolicy)
        6. 생성한 정책을 사용자에게 연결
        7. Security credentials 탭에서 Access key 생성
        8. Access key ID와 Secret access key를 안전하게 보관
        """
        
        self.info_box(steps_text, "info", "IAM User 및 Access Key 생성 단계")
        
        # 보안 주의사항
        self.info_box(
            "⚠️ Access Key는 장기 자격 증명입니다. 정기적으로 로테이션하고 "
            "불필요한 권한은 제거하여 보안을 유지하세요.",
            "warning",
            "보안 주의사항"
        )
    
    def render_step3(self) -> None:
        """3단계: 연결 정보 입력 렌더링"""
        st.markdown("### 📝 연결 정보를 입력해주세요")
        
        # 공통 필드
        self._render_common_fields()
        
        st.markdown("---")
        
        # 연결 방식별 필드
        connection_type = st.session_state.connection_type
        if connection_type == "cross-account-role":
            self._render_role_fields()
        elif connection_type == "access-key":
            self._render_access_key_fields()
        
        # 폼 검증
        self._validate_step3_form()
        
        # 네비게이션
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← 이전 단계", key="step3_prev"):
                self.safe_session_update('current_step', 2)
        
        with col2:
            form_valid, errors = self.engine.validate_connection_form(st.session_state.account_data)
            if st.button("연결 테스트 →", key="step3_next", type="primary", disabled=not form_valid):
                if form_valid:
                    self.safe_session_update('current_step', 4)
                else:
                    for error in errors[:3]:  # 최대 3개까지만 표시
                        st.error(error)
    
    def _render_common_fields(self) -> None:
        """공통 입력 필드 렌더링"""
        # 클라우드 이름
        cloud_name = st.text_input(
            "☁️ 클라우드 이름 *",
            value=st.session_state.account_data.get('cloud_name', ''),
            placeholder="예: 개발환경 AWS, 운영환경 AWS",
            help="이 AWS 계정을 구분할 수 있는 이름을 입력하세요"
        )
        if cloud_name != st.session_state.account_data.get('cloud_name', ''):
            st.session_state.account_data['cloud_name'] = cloud_name
        
        # 담당자 이메일
        contact_email = st.text_input(
            "📧 담당자 이메일 *",
            value=st.session_state.account_data.get('contact_email', ''),
            placeholder="example@company.com",
            help="이 AWS 계정의 담당자 이메일 주소"
        )
        if contact_email != st.session_state.account_data.get('contact_email', ''):
            st.session_state.account_data['contact_email'] = contact_email
            self.validate_and_show_error('email', contact_email)
        
        # 주 리전
        regions = get_available_regions()
        current_region = st.session_state.account_data.get('primary_region', 'ap-northeast-2')
        
        primary_region = st.selectbox(
            "🌏 주 리전 *",
            options=list(regions.keys()),
            index=list(regions.keys()).index(current_region) if current_region in regions else 0,
            format_func=lambda x: f"{x} - {regions[x]}",
            help="주로 사용하는 AWS 리전을 선택하세요"
        )
        if primary_region != st.session_state.account_data.get('primary_region'):
            st.session_state.account_data['primary_region'] = primary_region
    
    def _render_role_fields(self) -> None:
        """Cross-Account Role 필드 렌더링"""
        st.markdown("#### 🛡️ Cross-Account Role 정보")
        
        # Role ARN
        role_arn = st.text_input(
            "🔗 IAM Role ARN *",
            value=st.session_state.account_data.get('role_arn', ''),
            placeholder="arn:aws:iam::123456789012:role/WALBSecurityDiagnosisRole",
            help="2단계에서 생성한 IAM Role의 ARN을 입력하세요"
        )
        if role_arn != st.session_state.account_data.get('role_arn', ''):
            st.session_state.account_data['role_arn'] = role_arn
            self.validate_and_show_error('role_arn', role_arn)
            
            # Role ARN에서 계정 ID 자동 추출
            if role_arn:
                account_id = self.engine.extract_account_id_from_role_arn(role_arn)
                if account_id:
                    st.session_state.account_data['account_id'] = account_id
                    st.success(f"계정 ID가 자동으로 추출되었습니다: `{account_id}`")
        
        # External ID
        external_id = st.text_input(
            "🎯 External ID *",
            value=st.session_state.account_data.get('external_id', ''),
            placeholder="walb-xxxxxxxxxx",
            help="2단계에서 생성한 External ID를 입력하세요"
        )
        if external_id != st.session_state.account_data.get('external_id', ''):
            st.session_state.account_data['external_id'] = external_id
        
        # 계정 ID (자동 추출된 경우 읽기 전용)
        if st.session_state.account_data.get('account_id'):
            st.text_input(
                "🏢 AWS 계정 ID",
                value=st.session_state.account_data['account_id'],
                disabled=True,
                help="Role ARN에서 자동으로 추출된 계정 ID입니다"
            )
    
    def _render_access_key_fields(self) -> None:
        """Access Key 필드 렌더링"""
        st.markdown("#### 🔑 Access Key 정보")
        
        # Access Key ID
        access_key_id = st.text_input(
            "🔑 Access Key ID *",
            value=st.session_state.account_data.get('access_key_id', ''),
            placeholder="AKIA...",
            help="2단계에서 생성한 Access Key ID를 입력하세요"
        )
        if access_key_id != st.session_state.account_data.get('access_key_id', ''):
            st.session_state.account_data['access_key_id'] = access_key_id
            self.validate_and_show_error('access_key', access_key_id)
        
        # Secret Access Key (비밀번호 토글)
        self.input_field_with_toggle(
            "🔐 Secret Access Key *",
            "secret_access_key",
            placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            help="2단계에서 생성한 Secret Access Key를 입력하세요",
            is_password=True
        )
        
        # 계정 ID
        account_id = st.text_input(
            "🏢 AWS 계정 ID *",
            value=st.session_state.account_data.get('account_id', ''),
            placeholder="123456789012",
            help="12자리 AWS 계정 ID를 입력하세요"
        )
        if account_id != st.session_state.account_data.get('account_id', ''):
            st.session_state.account_data['account_id'] = account_id
            self.validate_and_show_error('account_id', account_id)
    
    def _validate_step3_form(self) -> None:
        """3단계 폼 실시간 검증"""
        form_valid, errors = self.engine.validate_connection_form(st.session_state.account_data)
        
        if not form_valid and any(field for field in st.session_state.account_data.values() if str(field).strip()):
            self.info_box(
                "입력 정보를 확인해주세요:\n" + "\n".join(f"• {error}" for error in errors[:3]),
                "warning",
                "입력 확인 필요"
            )
    
    def render_step4(self) -> None:
        """4단계: 연결 테스트 및 결과 표시"""
        st.markdown("### 🔬 AWS 연결 테스트")
        
        # 연결 정보 요약
        self._render_connection_summary()
        
        # 테스트 실행
        if st.session_state.connection_status == 'idle':
            self._render_test_start_button()
        elif st.session_state.connection_status == 'testing':
            self._render_testing_progress()
        elif st.session_state.connection_status == 'completed':
            self._render_test_results()
        
        # 네비게이션
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← 이전 단계", key="step4_prev"):
                self.safe_session_update('current_step', 3)
    
    def _render_connection_summary(self) -> None:
        """연결 정보 요약 표시"""
        account_data = st.session_state.account_data
        connection_type = st.session_state.connection_type
        
        st.markdown("#### 📋 연결 정보 확인")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**클라우드 이름:** {account_data.get('cloud_name', 'N/A')}")
            st.markdown(f"**연결 방식:** {get_connection_types()[connection_type]['title']}")
            st.markdown(f"**주 리전:** {account_data.get('primary_region', 'N/A')}")
        
        with col2:
            st.markdown(f"**계정 ID:** {account_data.get('account_id', 'N/A')}")
            st.markdown(f"**담당자:** {account_data.get('contact_email', 'N/A')}")
            
            if connection_type == "cross-account-role":
                st.markdown(f"**Role ARN:** {account_data.get('role_arn', 'N/A')[:50]}...")
            elif connection_type == "access-key":
                access_key = account_data.get('access_key_id', 'N/A')
                st.markdown(f"**Access Key:** {access_key[:8]}..." if len(access_key) > 8 else access_key)
    
    def _render_test_start_button(self) -> None:
        """테스트 시작 버튼 렌더링"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 연결 테스트 시작", key="start_test", type="primary", use_container_width=True):
                st.session_state.connection_status = 'testing'
                st.session_state.test_results = None
                st.rerun()
    
    def _render_testing_progress(self) -> None:
        """테스트 진행 중 표시"""
        st.markdown("---")
        
        # 로딩 스피너
        self.loading_spinner("AWS 연결을 테스트하고 있습니다...")
        
        # 테스트 실행
        connection_data = st.session_state.account_data.copy()
        connection_data['connection_type'] = st.session_state.connection_type
        
        # 실제 테스트 실행
        with st.spinner("연결 테스트 진행 중..."):
            test_results = self.engine.test_connection(connection_data)
        
        # 결과 저장 및 상태 변경
        st.session_state.test_results = test_results
        st.session_state.connection_status = 'completed'
        st.rerun()
    
    def _render_test_results(self) -> None:
        """테스트 결과 표시"""
        st.markdown("---")
        test_results = st.session_state.test_results
        
        if test_results.get('status') == 'success':
            st.success("✅ AWS 연결 테스트가 성공했습니다!")
            
            # 연결 정보
            if 'connection_info' in test_results:
                conn_info = test_results['connection_info']
                st.markdown(f"**연결된 계정:** `{conn_info.get('account_id', 'N/A')}`")
                st.markdown(f"**사용자 ARN:** `{conn_info.get('user_arn', 'N/A')}`")
                st.markdown(f"**리전:** `{conn_info.get('region', 'N/A')}`")
            
            # 서비스 테스트 결과
            if 'service_tests' in test_results:
                st.markdown("#### 🔍 서비스별 권한 테스트 결과")
                self.test_result_table(test_results['service_tests'])
            
            # 계정 등록 버튼
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔧 설정 수정", type="secondary", use_container_width=True):
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
                    self.safe_session_update('current_step', 3)
            
            with col2:
                if st.button("✅ 계정 등록 완료", type="primary", use_container_width=True):
                    self._register_account()
        
        else:
            st.error("❌ AWS 연결 테스트가 실패했습니다.")
            
            error_message = test_results.get('message', '알 수 없는 오류가 발생했습니다.')
            self.info_box(error_message, "error", "연결 실패")
            
            # 재시도 버튼
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 다시 테스트", key="retry_test", use_container_width=True):
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
                    st.rerun()
            
            with col2:
                if st.button("🔧 설정 수정", key="modify_settings", use_container_width=True):
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
                    self.safe_session_update('current_step', 3)
    
    def _register_account(self) -> None:
        """계정 등록 처리"""
        account_data = st.session_state.account_data.copy()
        account_data['connection_type'] = st.session_state.connection_type
        
        success, message = self.engine.register_account(account_data)
        
        if success:
            # 성공 애니메이션
            st.balloons()
            
            # Toast 메시지
            success_html = """
            <div id="toast" style="
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #10B981;
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                font-weight: bold;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                animation: fadein 0.5s, fadeout 0.5s 2.5s;
            ">
                🎉 AWS 계정이 성공적으로 등록되었습니다!
            </div>
            <style>
            @keyframes fadein {
                from { top: 0; opacity: 0; }
                to { top: 20px; opacity: 1; }
            }
            @keyframes fadeout {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            </style>
            <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 3000);
            </script>
            """
            components.html(success_html, height=0)
            
            # 세션 정리
            time.sleep(1)
            self.cleanup_sensitive_data()
            
        else:
            st.error(f"계정 등록 실패: {message}")
    
    def render_sidebar(self) -> None:
        """사이드바 패널 렌더링"""
        with st.sidebar:
            st.markdown("### 🔧 연결 상태")
            
            # 현재 단계 (안전한 접근)
            current_step = st.session_state.get('current_step', 1)
            step_info = self.config.get_step_by_number(current_step)
            st.markdown(f"**현재 단계:** {current_step}/4")
            st.markdown(f"**단계명:** {step_info.get('title', 'N/A')}")
            
            # 연결 방식 (안전한 접근)
            connection_type = st.session_state.get('connection_type', 'cross-account-role')
            type_info = get_connection_types().get(connection_type, {})
            st.markdown(f"**연결 방식:** {type_info.get('title', connection_type)}")
            
            # 연결 상태 (안전한 접근)
            status = st.session_state.get('connection_status', 'idle')
            status_emoji = {
                'idle': '⏳',
                'testing': '🔄', 
                'completed': '✅'
            }
            st.markdown(f"**테스트 상태:** {status_emoji.get(status, '❓')} {status}")
            
            st.markdown("---")
            
            # 디버깅 정보
            with st.expander("🐛 디버깅 정보"):
                account_data = st.session_state.get('account_data', {})
                test_results = st.session_state.get('test_results')
                
                st.json({
                    "current_step": st.session_state.get('current_step', 1),
                    "connection_type": st.session_state.get('connection_type', 'cross-account-role'),
                    "connection_status": st.session_state.get('connection_status', 'idle'),
                    "account_data_keys": list(account_data.keys()) if account_data else [],
                    "has_test_results": test_results is not None
                })
            
            # 세션 초기화
            if st.button("🔄 세션 초기화", use_container_width=True):
                from components.session_manager import SessionManager
                SessionManager.reset_connection_data(keep_aws_handler=True)
                st.rerun()
    
    # ================================
    # 컴포넌트 렌더링 (기존 connection_components.py)
    # ================================
    
    def step_indicator(self, current_step: int) -> None:
        """4단계 진행 표시기 컴포넌트"""
        steps = get_step_definitions()
        
        # 단계별 HTML 생성
        step_items_html = ""
        for i, step in enumerate(steps):
            # 단계 상태 결정
            if step["number"] < current_step:
                status = "completed"
                icon = "✅"
                circle_class = "step-completed"
                title_class = "title-completed"
            elif step["number"] == current_step:
                status = "active"
                icon = str(step["number"])
                circle_class = "step-active"
                title_class = "title-active"
            else:
                status = "pending"
                icon = str(step["number"])
                circle_class = "step-pending"
                title_class = "title-pending"
            
            # 단계 아이템 HTML
            step_items_html += f'''
            <div class="step-item">
                <div class="step-circle {circle_class}">{icon}</div>
                <span class="step-title {title_class}">{step["title"]}</span>
            </div>
            '''
            
            # 연결선 추가 (마지막 단계 제외)
            if i < len(steps) - 1:
                step_items_html += '<div class="step-connector"></div>'
        
        # HTML 렌더링
        step_html = get_step_indicator_template(step_items_html)
        components.html(step_html, height=120)
    
    def connection_type_card(self, title: str, subtitle: str, description: str, pros: str, 
                           is_selected: bool, icon: str, card_type: str = "role") -> None:
        """연결방식 선택 카드 컴포넌트"""
        # 보안 수준 결정
        security_level = "높음" if card_type == "role" else "보통"
        
        card_html = get_connection_type_card_template(
            title=title,
            description=description,
            pros=pros,
            is_selected=is_selected,
            icon=icon,
            security_level=security_level
        )
        
        components.html(card_html, height=200)
    
    def info_box(self, message: str, box_type: str, title: str = "") -> None:
        """정보/경고 박스 컴포넌트"""
        info_html = get_info_box_template(message, box_type, title)
        components.html(info_html, height=None)
    
    def json_code_block(self, json_data: Dict[str, Any], title: str) -> None:
        """JSON 코드 블록 컴포넌트"""
        # JSON 포맷팅
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # 동적 높이 계산
        line_count = len(formatted_json.split('\n'))
        dynamic_height = min(max(line_count * 20 + 100, 200), 600)
        
        json_html = get_json_code_block_template(formatted_json, title)
        components.html(json_html, height=dynamic_height)
    
    def test_result_table(self, test_results: List[Dict[str, Any]]) -> None:
        """연결 테스트 결과 테이블 컴포넌트"""
        # 테이블 행 HTML 생성
        table_rows_html = ""
        for result in test_results:
            service = result.get('service', 'Unknown')
            status = result.get('status', 'pending')
            message = result.get('message', 'N/A')
            response_time = result.get('response_time', 'N/A')
            
            # 상태별 CSS 클래스
            status_class = {
                'success': 'status-success',
                'failed': 'status-failed',
                'error': 'status-failed'
            }.get(status, 'status-pending')
            
            # 상태 표시 텍스트
            status_text = {
                'success': '✅ 성공',
                'failed': '❌ 실패', 
                'error': '❌ 오류'
            }.get(status, '⏳ 대기')
            
            table_rows_html += f"""
            <tr>
                <td>{service.upper()}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{message}</td>
                <td>{response_time}</td>
            </tr>
            """
        
        # 동적 높이 계산
        table_height = min(len(test_results) * 50 + 100, 400)
        
        table_html = get_test_result_table_template(table_rows_html)
        components.html(table_html, height=table_height)
    
    def loading_spinner(self, message: str) -> None:
        """로딩 스피너 컴포넌트"""
        spinner_html = get_loading_spinner_template(message)
        components.html(spinner_html, height=150)
    
    def input_field_with_toggle(self, label: str, key: str, placeholder: str = "", 
                               help: str = "", is_password: bool = True) -> None:
        """비밀번호 토글 입력 필드 컴포넌트"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if is_password and st.session_state.get(f'show_{key}', False):
                # 평문 표시
                value = st.text_input(
                    label,
                    value=st.session_state.account_data.get(key, ''),
                    placeholder=placeholder,
                    help=help,
                    key=f"input_{key}"
                )
            else:
                # 마스킹 표시
                value = st.text_input(
                    label,
                    value=st.session_state.account_data.get(key, ''),
                    placeholder=placeholder,
                    help=help,
                    type="password" if is_password else "default",
                    key=f"input_{key}"
                )
        
        with col2:
            if is_password:
                show_key = f'show_{key}'
                current_show = st.session_state.get(show_key, False)
                
                if st.button("👁️" if not current_show else "🙈", key=f"toggle_{key}"):
                    st.session_state[show_key] = not current_show
                    st.rerun()
        
        # 값 업데이트
        if value != st.session_state.account_data.get(key, ''):
            st.session_state.account_data[key] = value
            if key == 'secret_access_key':
                self.validate_and_show_error('secret_key', value)
    
    # ================================
    # 유틸리티 메서드
    # ================================
    
    def validate_and_show_error(self, field_type: str, value: str) -> None:
        """실시간 입력 검증 및 오류 표시"""
        if value.strip():
            is_valid, message = self.engine.validate_input_field(field_type, value)
            if is_valid:
                st.success(message)
            else:
                st.error(message)
    
    def safe_session_update(self, key: str, value: Any) -> None:
        """안전한 세션 상태 업데이트"""
        if st.session_state.get(key) != value:
            st.session_state[key] = value
            st.rerun()
    
    def get_actual_secret_key(self) -> str:
        """마스킹된 Secret Key의 실제값 반환"""
        return st.session_state.account_data.get('secret_access_key', '')
    
    def cleanup_sensitive_data(self) -> None:
        """보안을 위한 민감정보 자동 정리"""
        self.engine.cleanup_sensitive_data()
        
        # UI 관련 임시 데이터도 정리
        for key in list(st.session_state.keys()):
            if key.startswith('show_') or key.startswith('input_'):
                del st.session_state[key]