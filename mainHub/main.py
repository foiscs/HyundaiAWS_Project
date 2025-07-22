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
from components import *
from aws_handler import AWSConnectionHandler, InputValidator, simulate_connection_test
from styles import get_all_styles

# 페이지 설정
st.set_page_config(
    page_title="AWS 계정 연결 - WALB",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """
    세션 상태 초기화
    - 사용자의 진행 상태와 입력 데이터 관리
    """
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    if 'connection_type' not in st.session_state:
        st.session_state.connection_type = 'cross-account-role'
    
    if 'account_data' not in st.session_state:
        st.session_state.account_data = {
            'cloud_name': '',
            'account_id': '',
            'role_arn': '',
            'external_id': '',
            'access_key_id': '',
            'secret_access_key': '',
            'primary_region': 'ap-northeast-2',
            'contact_email': ''
        }

    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = 'idle'

    if 'test_results' not in st.session_state:
        st.session_state.test_results = None

    if 'aws_handler' not in st.session_state:
        st.session_state.aws_handler = AWSConnectionHandler()

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
        st.session_state.current_step = 2
        st.rerun()

def render_step2():
    """
    2단계: 권한 설정 가이드
    - IAM Role/User 설정 방법 안내
    """
    with st.container():
        if st.session_state.connection_type == 'cross-account-role':
            st.subheader("🛡️ IAM Role 설정 가이드")
            
            info_box(
                "대상 AWS 계정에서 수행할 작업:<br>"
                "1. IAM 콘솔에서 새 Role 생성 (예: WALB-SecurityAssessment)<br>"
                "2. 신뢰 관계에 아래 정책 적용<br>"
                "3. 권한 정책 연결<br>"
                "4. 생성된 Role ARN 복사",
                box_type="info",
                title="설정 순서"
            )
            
            # External ID 생성
            if not st.session_state.account_data['external_id']:
                st.session_state.account_data['external_id'] = st.session_state.aws_handler.generate_external_id()
            
            # Trust Policy 표시
            trust_policy = st.session_state.aws_handler.generate_trust_policy(
                st.session_state.account_data['external_id']
            )
            json_code_block(trust_policy, "1. 신뢰 관계 정책")
            
            # Permission Policy 표시
            permission_policy = st.session_state.aws_handler.generate_permission_policy()
            json_code_block(permission_policy, "2. 권한 정책")
            
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
                "4. 아래 권한 정책을 **정책 생성**으로 만들어서 연결<br>"
                "5. 사용자 생성 후 **Security credentials → Create access key**<br>"
                "6. **Use case: Third-party service** 선택 후 Access Key 다운로드",
                box_type="warning",
                title="설정 순서 (최신 AWS 콘솔)"
            )
            
            # Permission Policy 표시
            permission_policy = st.session_state.aws_handler.generate_permission_policy()
            json_code_block(permission_policy, "권한 정책")

        
        # 네비게이션 버튼
        prev_clicked, next_clicked = navigation_buttons(
            prev_label="이전",
            next_label="다음 단계"
        )
        
        if prev_clicked:
            st.session_state.current_step = 1
            st.rerun()
        
        if next_clicked:
            st.session_state.current_step = 3
            st.rerun()

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
        if account_id:
            is_valid, error_msg = InputValidator.validate_account_id(account_id)
            if not is_valid:
                st.error(error_msg)
        
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
            if role_arn:
                is_valid, error_msg = InputValidator.validate_role_arn(role_arn)
                if not is_valid:
                    st.error(error_msg)
        
        else:  # access-key
            col3, col4 = st.columns(2)
            
            with col3:
                access_key_id = st.text_input(
                    "Access Key ID *",
                    value=st.session_state.account_data['access_key_id'],
                    placeholder="AKIA...",
                    help="AWS Access Key ID를 입력하세요."
                )
                st.session_state.account_data['access_key_id'] = access_key_id
                
                # Access Key 검증
                if access_key_id:
                    is_valid, error_msg = InputValidator.validate_access_key(access_key_id)
                    if not is_valid:
                        st.error(error_msg)
            
            with col4:
                secret_access_key, show_secret = input_field_with_toggle(
                    "Secret Access Key *",
                    is_password=True,
                    help="AWS Secret Access Key를 입력하세요."
                )
                if secret_access_key != st.session_state.account_data['secret_access_key']:
                    st.session_state.account_data['secret_access_key'] = secret_access_key
                
                # Secret Key 검증
                if secret_access_key:
                    is_valid, error_msg = InputValidator.validate_secret_key(secret_access_key)
                    if not is_valid:
                        st.error(error_msg)
        
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
            if contact_email:
                is_valid, error_msg = InputValidator.validate_email(contact_email)
                if not is_valid:
                    st.error(error_msg)

        
        # 입력 완료 여부 확인
        required_fields_filled = bool(
            st.session_state.account_data['cloud_name'] and
            st.session_state.account_data['account_id']
        )
        
        if st.session_state.connection_type == 'cross-account-role':
            required_fields_filled = required_fields_filled and bool(
                st.session_state.account_data['role_arn']
            )
        else:
            required_fields_filled = required_fields_filled and bool(
                st.session_state.account_data['access_key_id'] and
                st.session_state.account_data['secret_access_key']
            )
        
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
            st.session_state.current_step = 4
            st.rerun()
        
def render_step4():
    """
    4단계: 연결 테스트
    - AWS 연결 테스트 실행 및 결과 표시
    """
    with st.container():
        st.subheader("🔍 연결 테스트")

        def run_connection_test():
            """연결 테스트 실행 함수"""
            st.session_state.connection_status = 'testing'
            st.session_state.test_results = None
            
            try:
                if st.session_state.connection_type == 'cross-account-role':
                    test_results = st.session_state.aws_handler.test_cross_account_connection(
                        role_arn=st.session_state.account_data['role_arn'],
                        external_id=st.session_state.account_data['external_id'],
                        region=st.session_state.account_data['primary_region']
                    )
                else:
                    test_results = st.session_state.aws_handler.test_access_key_connection(
                        access_key_id=st.session_state.account_data['access_key_id'],
                        secret_access_key=st.session_state.account_data['secret_access_key'],
                        region=st.session_state.account_data['primary_region']
                    )

                st.session_state.test_results = test_results
                st.session_state.connection_status = (
                    'success' if test_results['status'] == 'success' else 'failed'
                )
            except Exception as e:
                st.session_state.connection_status = 'failed'
                st.session_state.test_results = {
                    'status': 'failed',
                    'error_message': str(e)
                }

        # 상태 분기
        if st.session_state.connection_status == 'idle':
            prev_clicked, test_clicked = connection_test_result(
                st.session_state.test_results,
                st.session_state.connection_status
            )

            if prev_clicked:
                st.session_state.current_step = 3
                st.rerun()

            if test_clicked:
                with st.spinner("연결 테스트를 수행하고 있습니다..."):
                    # 실제 테스트
                    # run_connection_test()
                    time.sleep(3)
                    st.session_state.test_results = simulate_connection_test()
                    st.session_state.connection_status = 'success'
                st.rerun()

        elif st.session_state.connection_status == 'success':
            # 테스트 결과 출력
            test_result_table(st.session_state.test_results)

            # 계정 등록 완료 버튼만 출력 (다시 테스트 제거됨)
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("🔧 설정 수정", type="secondary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            with col2:
                if st.button("✅ 계정 등록 완료", type="primary", use_container_width=True):
                    account = st.session_state.account_data.copy()
                    try:
                        with open("registered_accounts.json", "a", encoding="utf-8") as f:
                            f.write(json.dumps(account, ensure_ascii=False) + "\n")
                        
                        # 🎈 먼저 벌룬 호출
                        st.balloons()

                        # ✅ Toast 메시지 출력 (components로)
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

                        # 리다이렉트 직전 상태 초기화 (단, JS에서 3초 뒤 리다이렉션 되므로 여기서 st.rerun() 제거)
                        for key in list(st.session_state.keys()):
                            if key.startswith(('current_step', 'connection_type', 'account_data', 'connection_status', 'test_results')):
                                del st.session_state[key]

                        st.stop()  # rerun 방지. toast 이후에 reload는 JS가 담당

                    except Exception as e:
                        st.error(f"파일 저장 중 오류 발생: {str(e)}")


                    # 상태 초기화 후 1단계로 이동
                    for key in list(st.session_state.keys()):
                        if key.startswith(('current_step', 'connection_type', 'account_data', 'connection_status', 'test_results')):
                            del st.session_state[key]
                    st.session_state.current_step = 1
                    st.rerun()



        elif st.session_state.connection_status == 'failed':
            prev_clicked, next_clicked = navigation_buttons(
                prev_label="설정 수정",
                next_label="다시 시도",
                prev_callback=lambda: setattr(st.session_state, 'current_step', 3),
                next_callback=lambda: [
                    setattr(st.session_state, 'connection_status', 'idle'),
                    setattr(st.session_state, 'test_results', None)
                ]
            )


def main():
    """
    메인 애플리케이션 함수
    - 세션 상태 초기화 및 페이지 라우팅
    """
    try:
        # CSS 스타일 주입
        st.markdown(get_all_styles(), unsafe_allow_html=True)
        
        # 세션 상태 초기화
        initialize_session_state()
        
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
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()