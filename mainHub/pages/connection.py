"""
AWS 계정 연결 웹 인터페이스 메인 애플리케이션
Streamlit을 사용한 4단계 온보딩 프로세스 구현

함수 목록:
- initialize_session_state: 사용자 진행 상태와 입력 데이터 세션 초기화
- render_header: 페이지 제목과 단계 표시기 헤더 렌더링
- render_step1: 1단계 - Cross-Account Role vs Access Key 연결 방식 선택
- render_step2: 2단계 - IAM Role/User 설정 가이드와 JSON 정책 표시
- render_step3: 3단계 - 계정 정보와 인증 정보 입력 폼 + 실시간 검증
- render_step4: 4단계 - AWS 연결 테스트 실행 및 결과 표시
- main: 메인 앱 함수 - CSS 주입, 세션 초기화, 페이지 라우팅
"""

import streamlit as st
import time
from components.connection_components import *
from components.aws_handler import AWSConnectionHandler, InputValidator, simulate_connection_test
from components.connection_styles import get_all_styles
from components.session_manager import SessionManager

# 페이지 설정
st.set_page_config(
    page_title="AWS 계정 연결 - WALB",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def safe_step_change(new_step):
    """안전한 단계 변경"""
    if st.session_state.current_step != new_step:
        st.session_state.current_step = new_step
        st.rerun()
        
def render_header():
    """
    페이지 헤더 렌더링
    - 제목과 단계 표시기 포함
    """
    # 헤더 컨테이너
    header_container = st.container()
    with header_container:
        st.markdown('''
        <div class="main-container">
            <div class="main-title">
                ☁️ 새 AWS 계정 연결
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 단계 표시기
        step_indicator(st.session_state.current_step)

def render_step1():
    """
    1단계: 연결 방식 선택
    - Cross-Account Role vs Access Key 선택
    """
    with st.container():
        st.subheader("🔗 연결 방식을 선택하세요")
        
        st.write("AWS 계정 연결을 위한 인증 방식을 선택해주세요.")
        
        # Cross-Account Role 카드
        role_selected = connection_type_card(
            title="Cross-Account Role (권장)",
            description="가장 안전한 방식입니다. AWS IAM Role을 통해 임시 권한을 부여받습니다.",
            pros=["✓ 높은 보안성", "✓ 권한 제어 가능", "✓ 감사 추적"],
            is_selected=(st.session_state.connection_type == 'cross-account-role'),
            icon="🛡️",
            card_type="role"
        )
        
        if role_selected:
            st.session_state.connection_type = 'cross-account-role'
            st.rerun()
        
        # Access Key 카드
        key_selected = connection_type_card(
            title="Access Key & Secret Key",
            description="간단하지만 보안 위험이 있습니다. 테스트 환경에서만 권장합니다.",
            pros=["⚠ 보안 위험", "⚠ 키 관리 필요", "✓ 설정 간단"],
            is_selected=(st.session_state.connection_type == 'access-key'),
            icon="🔑",
            card_type="key"
        )
        
        if key_selected:
            st.session_state.connection_type = 'access-key'
            st.rerun()
    
    # 네비게이션 버튼
    prev_clicked, next_clicked = navigation_buttons(
        show_prev=False,
        next_label="다음 단계"
    )
    
    if next_clicked:
        safe_step_change(2)

def render_step2():
    """
    2단계: 권한 설정 가이드
    - IAM Role/User 설정 방법 안내
    """
    with st.container():
        if st.session_state.connection_type == 'cross-account-role':
            st.subheader("🛡️ IAM Role 설정 가이드")
            
            info_box(
                "**🎯 간단한 3단계 설정으로 완료!**<br><br>"
                "**1단계**: IAM 콘솔 → Roles → Create role<br>"
                "**2단계**: 신뢰할 수 있는 엔터티 설정<br>"
                "• **AWS 계정** 선택<br>"
                "• **다른 AWS 계정** 선택<br>"
                "• **계정 ID**: 292967571836<br>"
                "• **외부 ID 필요** ✅ 체크<br>"
                "• **외부 ID**: 아래 표시된 값 입력<br><br>"
                "**3단계**: 권한 정책 연결<br>"
                "• **AdministratorAccess** 검색해서 선택<br>"
                "• **역할 이름**: WALB-CrossAccount-Role<br>"
                "• **역할 생성** 완료",
                box_type="success",
                title="AWS 콘솔 설정 가이드"
            )
            
            # External ID 생성 및 표시
            if not st.session_state.account_data['external_id']:
                st.session_state.account_data['external_id'] = st.session_state.aws_handler.generate_external_id()
            
            # External ID를 눈에 띄게 표시
            st.markdown("### 🔑 외부 ID (External ID)")
            st.code(st.session_state.account_data['external_id'], language=None)
            st.info("💡 위 외부 ID를 AWS 콘솔의 **'외부 ID'** 필드에 복사해서 붙여넣으세요.")
            
            # Trust Policy 자동 생성 안내
            info_box(
                "✨ **Trust Policy는 AWS 콘솔이 자동으로 생성합니다**<br><br>"
                "위 단계대로 설정하면 AWS가 올바른 신뢰 관계 정책을 자동으로 만들어줍니다.<br>"
                "**JSON 코드를 직접 붙여넣을 필요가 없어요!**<br><br>"
                "🎯 **완료 후**: 생성된 Role의 **ARN**을 복사해서 다음 단계에서 사용하세요.",
                box_type="info",
                title="자동 생성되는 Trust Policy"
            )
            
            # External ID 안내
            info_box(
                f"External ID: <code>{st.session_state.account_data['external_id']}</code><br>"
                "이 값을 Role 설정 시 사용하세요.",
                box_type="warning",
                title="중요한 정보"
            )
            
        else:  # access-key
            st.subheader("🔑 IAM 사용자 설정 가이드")
            
            info_box(
                "대상 AWS 계정에서 수행할 작업:<br>"
                "1. **IAM 콘솔 → Users → Create user**<br>"
                "2. **사용자 이름** 입력 (예: walb-service-user)<br>"
                "3. **권한 설정 → 직접 정책 연결** 선택<br>"
                "4. **AdministratorAccess** 검색해서 체크박스 선택<br>"
                "5. 사용자 생성 후 **Security credentials → Create access key**<br>"
                "6. **Use case: Third-party service** 선택 후 Access Key 다운로드",
                box_type="warning",
                title="설정 순서"
            )
            
            # AdministratorAccess 정책 안내 (JSON 불필요)
            info_box(
                "**권한 정책**: AWS 관리형 정책 **AdministratorAccess**를 연결하세요.<br>"
                "• 'AdministratorAccess'를 검색해서 체크박스 선택<br>"
                "• JSON 복붙 불필요 - 클릭 한 번이면 끝<br>"
                "• 모든 AWS 서비스에 대한 완전한 관리자 권한",
                box_type="success",
                title="권한 설정 (매우 간단함)"
            )
        
        # 네비게이션 버튼
        prev_clicked, next_clicked = navigation_buttons(
            prev_label="이전",
            next_label="다음 단계"
        )
        
        if prev_clicked:
            st.session_state.current_step = 1
            st.rerun()
        
        if next_clicked:
            safe_step_change(3)

def render_step3():
    """
    3단계: 연결 정보 입력
    - 계정 정보와 인증 정보 입력 폼
    """
    with st.container():
        st.subheader("📝 연결 정보를 입력하세요")
        
        # 기본 정보 입력
        col1, col2 = st.columns(2)
        
        with col1:
            cloud_name = st.text_input(
                "클라우드 환경 이름 *",
                value=st.session_state.account_data['cloud_name'],
                placeholder="예: 김청소 개인계정, 개발용 환경",
                help="WALB에서 이 AWS 계정을 구분할 수 있는 별명을 입력하세요."
            )
            st.session_state.account_data['cloud_name'] = cloud_name
        
        with col2:
            account_id = st.text_input(
                "AWS 계정 ID *",
                value=st.session_state.account_data['account_id'],
                placeholder="123456789012",
                help="12자리 숫자 계정 ID입니다. AWS 콘솔 우상단 → 계정명 클릭 → Account ID에서 확인하세요."
            )
            st.session_state.account_data['account_id'] = account_id
                
        # 계정 ID 검증
        validate_and_show_error("account_id", account_id, InputValidator.validate_account_id)
        
        # 연결 방식별 입력 필드
        if st.session_state.connection_type == 'cross-account-role':
            role_arn = st.text_input(
                "Role ARN *",
                value=st.session_state.account_data['role_arn'],
                placeholder="arn:aws:iam::123456789012:role/WALB-SecurityAssessment",
                help="2단계에서 생성한 IAM Role의 ARN을 입력하세요."
            )
            st.session_state.account_data['role_arn'] = role_arn
            
            # Role ARN 검증
            validate_and_show_error("role_arn", role_arn, InputValidator.validate_role_arn)
        
        else:  # access-key
            col3, col4 = st.columns(2)
            
            with col3:
                access_key_id = st.text_input(
                    "Access Key ID *",
                    value=st.session_state.account_data['access_key_id'],
                    placeholder="AKIA...",
                    help="AWS Access Key ID를 입력하세요."
                )
                # 실시간 정리
                access_key_id = access_key_id.strip() if access_key_id else ''
                st.session_state.account_data['access_key_id'] = access_key_id
                
                # Access Key 검증
                validate_and_show_error("access_key", access_key_id, InputValidator.validate_access_key)
            
            with col4:
                secret_access_key, show_secret, has_security_warning = input_field_with_toggle(
                    "Secret Access Key *",
                    is_password=True,
                    help="AWS Secret Access Key를 입력하세요."
                )
                # 민감 정보는 세션에 저장하지 않고 즉시 사용
                if secret_access_key:
                    st.session_state.temp_secret_key = secret_access_key
                    st.session_state.account_data['secret_access_key'] = '[MASKED]'
                    st.info("🔒 Secret Key는 보안을 위해 임시 저장됩니다.")
                
                # 실제 입력된 Secret Key로 검증 (마스킹 전)
                if secret_access_key:
                    validate_and_show_error("secret_key", secret_access_key, InputValidator.validate_secret_key)
        
        # 추가 설정
        col5, col6 = st.columns(2)
        
        with col5:
            primary_region = st.selectbox(
                "기본 리전 *",
                options=[
                    'ap-northeast-2',  # Seoul
                    'us-east-1',       # N. Virginia
                    'us-west-2',       # Oregon
                    'eu-west-1',       # Ireland
                    'ap-southeast-1',  # Singapore
                    'ap-northeast-1',  # Tokyo
                ],
                format_func=lambda x: {
                    'ap-northeast-2': 'Asia Pacific (Seoul)',
                    'us-east-1': 'US East (N. Virginia)',
                    'us-west-2': 'US West (Oregon)',
                    'eu-west-1': 'Europe (Ireland)',
                    'ap-southeast-1': 'Asia Pacific (Singapore)',
                    'ap-northeast-1': 'Asia Pacific (Tokyo)'
                }.get(x, x),
                index=0,
                help="AWS 리소스가 주로 위치한 리전을 선택하세요."
            )
            st.session_state.account_data['primary_region'] = primary_region
        
        with col6:
            contact_email = st.text_input(
                "담당자 이메일",
                value=st.session_state.account_data['contact_email'],
                placeholder="admin@company.com",
                help="연락 가능한 담당자 이메일을 입력하세요. (선택사항)"
            )
            st.session_state.account_data['contact_email'] = contact_email
            
            # 이메일 검증
            validate_and_show_error("email", contact_email, InputValidator.validate_email)

        
        # 수정 (new) - 위 블록을 아래로 교체
        def check_required_fields():
            """필수 입력 필드 완료 여부 확인"""
            account = st.session_state.account_data
            basic_filled = bool(account['cloud_name'] and account['account_id'])
            
            if st.session_state.connection_type == 'cross-account-role':
                return basic_filled and bool(account['role_arn'])
            else:
                return basic_filled and bool(account['access_key_id'] and account['secret_access_key'])

        # 입력 완료 여부 확인
        required_fields_filled = check_required_fields()
        
        # 네비게이션 버튼
        prev_clicked, next_clicked = navigation_buttons(
            prev_label="이전",
            next_label="연결 테스트",
            next_disabled=not required_fields_filled
        )
        
        if prev_clicked:
            st.session_state.current_step = 2
            st.rerun()
        
        if next_clicked:
            safe_step_change(4)
        
def render_step4():
    """
    4단계: 연결 테스트
    - AWS 연결 테스트 실행 및 결과 표시
    """
    with st.container():
        st.subheader("🔍 연결 테스트")

        # 연결 테스트 실행 함수
        def run_connection_test():
            """실제 AWS API를 통한 연결 테스트"""
            try:
                if st.session_state.connection_type == 'cross-account-role':
                    test_results = st.session_state.aws_handler.test_cross_account_connection(
                        role_arn=st.session_state.account_data['role_arn'],
                        external_id=st.session_state.account_data['external_id'],
                        region=st.session_state.account_data['primary_region']
                    )
                else:
                    # 실제 Secret Key 가져오기
                    actual_secret_key = st.session_state.get('temp_secret_key', '') or st.session_state.account_data.get('secret_access_key', '')
                    if actual_secret_key == '[MASKED]':
                        actual_secret_key = st.session_state.get('temp_secret_key', '')

                    test_results = st.session_state.aws_handler.test_access_key_connection(
                        access_key_id=st.session_state.account_data['access_key_id'],
                        secret_access_key=actual_secret_key,
                        region=st.session_state.account_data['primary_region']
                    )
                return test_results
            except Exception as e:
                return {
                    'status': 'failed',
                    'error_message': str(e)
                }

        # 상태별 UI 처리
        if st.session_state.connection_status == 'idle':
            # 테스트 준비 상태
            prev_clicked, test_clicked = connection_test_result(
                st.session_state.test_results,
                st.session_state.connection_status
            )

            if prev_clicked:
                st.session_state.current_step = 3
                st.rerun()

            if test_clicked:
                # 중복 클릭 방지
                if st.session_state.connection_status == 'idle':
                    st.session_state.connection_status = 'testing'
                    st.rerun()

        elif st.session_state.connection_status == 'testing':
            # 테스트 진행 중
            with st.spinner("🔄 연결 테스트를 수행하고 있습니다..."):
                # 개발 모드 확인
                is_development = st.secrets.get("DEVELOPMENT_MODE", True)
                
                if is_development:
                    # 개발 모드: 시뮬레이션
                    time.sleep(2)
                    st.session_state.test_results = simulate_connection_test()
                    st.session_state.connection_status = 'success'
                else:
                    # 실제 API 호출
                    test_results = run_connection_test()
                    st.session_state.test_results = test_results
                    st.session_state.connection_status = (
                        'success' if test_results['status'] == 'success' else 'failed'
                    )
                
                # 자동으로 결과 페이지로 이동
                time.sleep(1)
                st.rerun()

        elif st.session_state.connection_status == 'success':
            # 테스트 성공
            st.success("✅ 연결 성공! AWS 계정에 성공적으로 연결되었습니다.")
            
            # 테스트 결과 표시
            test_result_table(st.session_state.test_results)

            # 버튼 배치
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("🔧 설정 수정", type="secondary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            with col2:
                if st.button("✅ 계정 등록 완료", type="primary", use_container_width=True):
                    # 계정 등록 처리
                    account = st.session_state.account_data.copy()
                    
                    try:
                        # 파일에 저장 (Secret Key 포함)
                        with open("registered_accounts.json", "a", encoding="utf-8") as f:
                            f.write(json.dumps(account, ensure_ascii=False) + "\n")
                        
                        st.info("🔒 **보안 알림**: Secret Access Key가 로컬 파일에 저장됩니다.")
                        
                        # 성공 애니메이션
                        st.balloons()
                        
                        # Toast 메시지
                        components.html("""
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
                        """, height=100)

                        # 세션 초기화 후 3초 대기
                        time.sleep(3)
                        from components.session_manager import SessionManager
                        SessionManager.reset_connection_data()
                        st.switch_page("main.py")

                    except Exception as e:
                        st.error(f"파일 저장 중 오류 발생: {str(e)}")

        elif st.session_state.connection_status == 'failed':
            # 테스트 실패
            st.error("❌ 연결 실패 - 설정을 다시 확인해주세요.")
            
            # 실패 원인 표시
            if st.session_state.test_results and 'error_message' in st.session_state.test_results:
                st.error(f"오류 내용: {st.session_state.test_results['error_message']}")
            
            # 버튼 배치
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔧 설정 수정", type="secondary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            with col2:
                if st.button("🔄 다시 시도", type="primary", use_container_width=True):
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
                    st.rerun()
        
def main():
    """
    메인 애플리케이션 함수
    - 세션 상태 초기화 및 페이지 라우팅
    """
    try:
        # CSS 스타일 주입
        st.markdown(get_all_styles(), unsafe_allow_html=True)
        
        # 세션 상태 초기화
        SessionManager.initialize_session()
        
        # 헤더 렌더링
        render_header()
        
        # 메인 컨텐츠 컨테이너
        main_container = st.container()
        with main_container:
            # 현재 단계에 따른 페이지 렌더링
            if st.session_state.current_step == 1:
                render_step1()
            elif st.session_state.current_step == 2:
                render_step2()
            elif st.session_state.current_step == 3:
                render_step3()
            elif st.session_state.current_step == 4:
                render_step4()
            else:
                # 예외 상황 처리
                st.error("잘못된 단계입니다. 다시 시작해주세요.")
                if st.button("🔄 처음부터 시작"):
                    st.session_state.current_step = 1
                    st.rerun()
        
        # 사이드바 패널 렌더링
        sidebar_panel()
        
    except Exception as e:
        st.error(f"애플리케이션 오류가 발생했습니다: {str(e)}")
        st.write("페이지를 새로고침하거나 아래 버튼을 클릭하여 다시 시도해주세요.")
        if st.button("🔄 다시 시작"):
            SessionManager.reset_all(keep_aws_handler=False)
            st.rerun()

if __name__ == "__main__":
    main()