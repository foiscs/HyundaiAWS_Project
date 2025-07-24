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
        # Components로 세련된 헤더 렌더링
        header_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            }}
            .hero-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2.5rem 2rem;
                border-radius: 16px;
                margin: 1rem 0 2rem 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }}
            .hero-header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                opacity: 0.3;
            }}
            .hero-content {{
                position: relative;
                z-index: 2;
                display: flex;
                align-items: center;
                gap: 1.5rem;
            }}
            .hero-icon {{
                font-size: 3.5rem;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
                animation: float 3s ease-in-out infinite;
            }}
            .hero-text {{
                flex: 1;
            }}
            .hero-title {{
                font-size: 2.25rem;
                font-weight: 700;
                margin: 0 0 0.5rem 0;
                background: linear-gradient(45deg, #ffffff, #e0e7ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .hero-subtitle {{
                font-size: 1.1rem;
                opacity: 0.9;
                margin: 0;
                font-weight: 400;
            }}
            .hero-badge {{
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
                font-weight: 500;
                display: inline-block;
                margin-top: 0.75rem;
            }}
            .floating-elements {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                pointer-events: none;
                overflow: hidden;
            }}
            .floating-circle {{
                position: absolute;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                animation: float-circle 6s ease-in-out infinite;
            }}
            .circle-1 {{
                width: 60px;
                height: 60px;
                top: 20%;
                right: 10%;
                animation-delay: 0s;
            }}
            .circle-2 {{
                width: 40px;
                height: 40px;
                top: 60%;
                right: 20%;
                animation-delay: 2s;
            }}
            .circle-3 {{
                width: 80px;
                height: 80px;
                top: 10%;
                left: 15%;
                animation-delay: 4s;
            }}
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            @keyframes float-circle {{
                0%, 100% {{ transform: translateY(0px) scale(1); opacity: 0.3; }}
                50% {{ transform: translateY(-20px) scale(1.1); opacity: 0.6; }}
            }}
            </style>
        </head>
        <body>
            <div class="hero-header">
                <div class="floating-elements">
                    <div class="floating-circle circle-1"></div>
                    <div class="floating-circle circle-2"></div>
                    <div class="floating-circle circle-3"></div>
                </div>
                <div class="hero-content">
                    <div class="hero-icon">☁️</div>
                    <div class="hero-text">
                        <h1 class="hero-title">새 AWS 계정 연결</h1>
                        <p class="hero-subtitle">안전하고 간편한 클라우드 보안 관리를 시작하세요</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Components로 렌더링
        components.html(header_html, height=200)
        
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
            st.subheader("🛡️ Cross-Account Role 설정 가이드")
            st.markdown("""
            다음은 **WALB가 Role을 Assume하기 위해 필요한 최소 설정**입니다. 아래 **3단계**를 정확히 따라 수행해주세요.
            """)
            info_box(
                """
                <ol style="margin-bottom: 0;">
                <li><strong>IAM 콘솔 → Roles → Create role</strong></li>
                <li><strong>신뢰할 수 있는 엔터티 유형</strong>: 사용자 지정 신뢰 정책 ✅</li>
                <li><strong>아래 JSON을 복사하여 신뢰 정책란에 붙여넣기</strong></li>
                </ol>
                """,
                box_type="warning", 
                title="Step 1 - 사용자 지정 신뢰 정책으로 Role 생성"
            )

            # External ID 표시
            external_id = st.session_state.account_data['external_id']
            if not external_id:
                external_id = st.session_state.aws_handler.generate_external_id()
                st.session_state.account_data['external_id'] = external_id

            # 실제 JSON Trust Policy 출력
            trust_policy = st.session_state.aws_handler.generate_trust_policy(external_id)
            json_code_block(trust_policy, "신뢰 관계 정책 (Trust Policy)")

            info_box(
                """
                <strong>1.</strong> 권한 정책 부여: <code>AdministratorAccess</code> 검색 → 선택<br>
                <strong>2.</strong> 역할 이름 예시: <code>WALB-CrossAccount-Role</code><br>
                <strong>3.</strong> 생성 완료 후, <strong>Role ARN</strong>을 복사하여 다음 단계에서 입력하세요.
                """,
                box_type="success",
                title="Step 2 - 권한 정책 부여 및 Role 생성 완료"
            )
            st.markdown("---")
            
        else:  # access-key
            st.subheader("🔑 Access Key & Secret Key 설정 가이드")
            st.markdown("AWS 콘솔에서 **WALB용 IAM 사용자를 생성**하고 **Access Key를 발급**받으세요.")
            
            info_box(
                """
                <strong>1.</strong> IAM 콘솔 → Users → Create user<br>
                <strong>2.</strong> 사용자 이름 예시: <code>walb-diagnosis-service</code><br> 
                <strong>3.</strong> 권한 설정 → 직접 정책 연결 → <strong>AdministratorAccess</strong> 검색 후 선택<br>
                <strong>4.</strong> 사용자 생성 완료<br>
                <strong>5.</strong> Security credentials → Create access key → <strong>Third-party service</strong> 선택<br>
                <strong>6.</strong> <strong>Access Key CSV 다운로드</strong> 후 다음 단계에서 입력
                """,
                box_type="info",
                title="설정 단계"
            )
            
            info_box(
                """
                💡 <strong>AdministratorAccess 정책</strong>은 AWS 관리형 정책입니다.<br>
                • JSON 복사-붙여넣기 불필요<br>
                • 검색해서 체크박스만 선택하면 완료<br>
                • 모든 AWS 서비스에 대한 완전한 관리자 권한 제공
                """,
                box_type="success",
                title="권한 정책 안내"
            )
            st.markdown("---")
        
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
        
        # 기본 정보 입력 (연결 방식 무관하게 동일)
        cloud_name = st.text_input(
            "클라우드 환경 이름 *",
            value=st.session_state.account_data['cloud_name'],
            placeholder="예: 김청소 개인계정, 개발용 환경",
            help="WALB에서 이 AWS 계정을 구분할 수 있는 별명을 입력하세요."
        )
        st.session_state.account_data['cloud_name'] = cloud_name
        
        # 계정 ID는 자동으로 감지됨을 안내
        if st.session_state.connection_type == 'cross-account-role':
            st.info("💡 **계정 ID 자동 감지**: Role ARN에서 AWS 계정 ID를 자동으로 추출합니다.")
        else:
            st.info("💡 **계정 ID 자동 감지**: Access Key 연결 시 AWS 계정 ID는 자동으로 확인됩니다.")
                    
        # 연결 방식별 입력 필드
        if st.session_state.connection_type == 'cross-account-role':
            role_arn = st.text_input(
                "Role ARN *",
                value=st.session_state.account_data['role_arn'],
                placeholder="arn:aws:iam::123456789012:role/WALB-SecurityAssessment",
                help="2단계에서 생성한 IAM Role의 ARN을 입력하세요."
            )
            st.session_state.account_data['role_arn'] = role_arn
            
            # Role ARN에서 계정 ID 자동 추출
            if role_arn and st.session_state.aws_handler:
                extracted_account_id = st.session_state.aws_handler.extract_account_id_from_role_arn(role_arn)
                if extracted_account_id:
                    st.session_state.account_data['account_id'] = extracted_account_id
            
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
            cloud_name_filled = bool(account['cloud_name'])
            
            if st.session_state.connection_type == 'cross-account-role':
                return cloud_name_filled and bool(account['role_arn'])
            else:
                return cloud_name_filled and bool(account['access_key_id'] and account['secret_access_key'])

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
                st.session_state.connection_status = 'idle'
                st.session_state.test_results = None
                st.session_state.current_step = 3
                st.rerun()

            if test_clicked:
                # 중복 클릭 방지
                if st.session_state.connection_status == 'idle':
                    st.session_state.connection_status = 'testing'
                    st.rerun()

        elif st.session_state.connection_status == 'testing':
            # 기본 스피너 숨기기 CSS
            st.markdown('''
                <style>
                /* Streamlit 기본 스피너 완전히 숨기기 */
                .stSpinner {
                    display: none !important;
                }
                div[data-testid="stSpinner"] {
                    display: none !important;
                }
                .streamlit-spinner {
                    display: none !important;
                }
                </style>
                ''', unsafe_allow_html=True)
            
            # 테스트 진행 중 - 중앙 정렬된 커스텀 스피너
            st.markdown('''
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 3rem 1rem;
                    text-align: center;
                ">
                    <div style="
                        font-size: 3rem;
                        animation: spin 2s linear infinite;
                        margin-bottom: 1.5rem;
                    ">🔄</div>
                    <div style="
                        font-size: 1.25rem;
                        font-weight: 600;
                        color: #3B82F6;
                        margin-bottom: 0.5rem;
                    ">연결 테스트를 수행하고 있습니다</div>
                    <div style="
                        font-size: 0.875rem;
                        color: #6B7280;
                    ">AWS API 호출 및 권한 검증 중...</div>
                </div>
                
                <style>
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                </style>
                ''', unsafe_allow_html=True)
            
            with st.spinner(""):  # 빈 스피너로 실제 처리 (이제 안 보임)
                # 개발 모드 확인
                is_development = st.secrets.get("DEVELOPMENT_MODE", False)
                print(f"Development mode: {is_development}")
                
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
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
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
                    st.session_state.connection_status = 'idle'
                    st.session_state.test_results = None
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