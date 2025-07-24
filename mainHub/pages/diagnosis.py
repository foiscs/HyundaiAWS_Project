"""
WALB SK Shieldus 41개 항목 보안 진단 페이지
boto3 + Terraform 하이브리드 기반 AWS 인프라 보안 자동화
"""

import streamlit as st
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from components.sk_diagnosis import get_checker
from components.aws_handler import AWSConnectionHandler
from components.session_manager import SessionManager
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="보안 진단 - WALB",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_sk_shieldus_items():
    """SK Shieldus 41개 진단 항목 반환"""
    return {
        "계정 관리": [
            {"code": "1.1", "name": "사용자 계정 관리", "importance": "상", "description": "AWS 계정 및 IAM 사용자 권한 관리"},
            {"code": "1.2", "name": "IAM 사용자 계정 단일화 관리", "importance": "상", "description": "1인 1계정 원칙 준수"},
            {"code": "1.3", "name": "IAM 사용자 계정 식별 관리", "importance": "중", "description": "사용자 태그 및 식별 정보 설정"},
            {"code": "1.4", "name": "IAM 그룹 사용자 계정 관리", "importance": "중", "description": "IAM 그룹 기반 권한 관리"},
            {"code": "1.5", "name": "Key Pair 접근 관리", "importance": "상", "description": "EC2 Key Pair를 통한 안전한 접근"},
            {"code": "1.6", "name": "Key Pair 보관 관리", "importance": "상", "description": "Key Pair 파일의 안전한 보관"},
            {"code": "1.7", "name": "Admin Console 관리자 정책 관리", "importance": "중", "description": "관리자 계정의 적절한 사용"},
            {"code": "1.8", "name": "Admin Console 계정 Access Key 활성화 및 사용주기 관리", "importance": "상", "description": "Access Key 생명주기 관리"},
            {"code": "1.9", "name": "MFA (Multi-Factor Authentication) 설정", "importance": "중", "description": "다중 인증 활성화"},
            {"code": "1.10", "name": "AWS 계정 패스워드 정책 관리", "importance": "중", "description": "강력한 패스워드 정책 설정"},
            {"code": "1.11", "name": "EKS 사용자 관리", "importance": "상", "description": "EKS Cluster 사용자 권한 관리"},
            {"code": "1.12", "name": "EKS 서비스 어카운트 관리", "importance": "중", "description": "Kubernetes 서비스 어카운트 관리"},
            {"code": "1.13", "name": "EKS 불필요한 익명 접근 관리", "importance": "상", "description": "익명 사용자 접근 차단"}
        ],
        "권한 관리": [
            {"code": "2.1", "name": "인스턴스 서비스 정책 관리", "importance": "상", "description": "EC2, RDS, S3 등 서비스별 권한 관리"},
            {"code": "2.2", "name": "네트워크 서비스 정책 관리", "importance": "상", "description": "VPC, Route53 등 네트워크 권한 관리"},
            {"code": "2.3", "name": "기타 서비스 정책 관리", "importance": "상", "description": "CloudWatch, CloudTrail 등 기타 서비스 권한"}
        ],
        "가상 리소스 관리": [
            {"code": "3.1", "name": "보안 그룹 인/아웃바운드 ANY 설정 관리", "importance": "상", "description": "보안 그룹의 ANY 포트 허용 관리"},
            {"code": "3.2", "name": "보안 그룹 인/아웃바운드 불필요 정책 관리", "importance": "상", "description": "불필요한 보안 그룹 규칙 정리"},
            {"code": "3.3", "name": "네트워크 ACL 인/아웃바운드 트래픽 정책 관리", "importance": "중", "description": "Network ACL 트래픽 제어"},
            {"code": "3.4", "name": "라우팅 테이블 정책 관리", "importance": "중", "description": "라우팅 테이블 보안 설정"},
            {"code": "3.5", "name": "인터넷 게이트웨이 연결 관리", "importance": "하", "description": "IGW 연결 상태 관리"},
            {"code": "3.6", "name": "NAT 게이트웨이 연결 관리", "importance": "중", "description": "NAT Gateway 연결 관리"},
            {"code": "3.7", "name": "S3 버킷/객체 접근 관리", "importance": "중", "description": "S3 퍼블릭 액세스 차단 및 ACL 관리"},
            {"code": "3.8", "name": "RDS 서브넷 가용 영역 관리", "importance": "중", "description": "RDS 서브넷 그룹 보안 관리"},
            {"code": "3.9", "name": "EKS Pod 보안 정책 관리", "importance": "상", "description": "Pod Security Standards 적용"},
            {"code": "3.10", "name": "ELB(Elastic Load Balancing) 연결 관리", "importance": "중", "description": "로드밸런서 보안 설정"}
        ],
        "운영 관리": [
            {"code": "4.1", "name": "EBS 및 볼륨 암호화 설정", "importance": "중", "description": "스토리지 암호화 활성화"},
            {"code": "4.2", "name": "RDS 암호화 설정", "importance": "중", "description": "데이터베이스 암호화 설정"},
            {"code": "4.3", "name": "S3 암호화 설정", "importance": "중", "description": "S3 버킷 기본 암호화 설정"},
            {"code": "4.4", "name": "통신구간 암호화 설정", "importance": "중", "description": "전송 중 데이터 암호화"},
            {"code": "4.5", "name": "CloudTrail 암호화 설정", "importance": "중", "description": "CloudTrail 로그 암호화"},
            {"code": "4.6", "name": "CloudWatch 암호화 설정", "importance": "중", "description": "CloudWatch 로그 암호화"},
            {"code": "4.7", "name": "AWS 사용자 계정 로깅 설정", "importance": "상", "description": "사용자 활동 로그 기록"},
            {"code": "4.8", "name": "인스턴스 로깅 설정", "importance": "중", "description": "EC2 인스턴스 로그 수집"},
            {"code": "4.9", "name": "RDS 로깅 설정", "importance": "중", "description": "데이터베이스 로그 수집"},
            {"code": "4.10", "name": "S3 버킷 로깅 설정", "importance": "중", "description": "S3 액세스 로그 활성화"},
            {"code": "4.11", "name": "VPC 플로우 로깅 설정", "importance": "중", "description": "VPC 네트워크 플로우 로그"},
            {"code": "4.12", "name": "로그 보관 기간 설정", "importance": "중", "description": "로그 보존 정책 설정"},
            {"code": "4.13", "name": "백업 사용 여부", "importance": "중", "description": "백업 정책 수립 및 적용"},
            {"code": "4.14", "name": "EKS Cluster 제어 플레인 로깅 설정", "importance": "중", "description": "EKS 제어 플레인 로그 활성화"},
            {"code": "4.15", "name": "EKS Cluster 암호화 설정", "importance": "중", "description": "EKS Secrets 암호화 설정"}
        ]
    }

importance_colors = {
    "상": "🔴",
    "중": "🟡", 
    "하": "🟢"
}
    
def render_diagnosis_item(item, category, index):
    """진단 항목 카드 렌더링 - 실시간 진단 포함"""
    importance_color = importance_colors.get(item["importance"], "⚪")
    item_key = f"{category}_{index}"
    
    with st.container():
        # 진단 상태 확인
        diagnosis_status = st.session_state.get(f'diagnosis_status_{item_key}', 'idle')
        diagnosis_result = st.session_state.get(f'diagnosis_result_{item_key}', None)
        
        col1, col2, col3 = st.columns([4, 2, 1])
        
        with col1:
            st.markdown(f"**{item['code']}** {item['name']}")
            st.write(f"📝 {item['description']}")
            
        with col2:
            st.write(f"**중요도:** {importance_color} {item['importance']}")
            
            # 상태 표시
            if diagnosis_status == 'idle':
                st.write("**상태:** ⏳ 대기중")
            elif diagnosis_status == 'running':
                st.write("**상태:** 🔄 진단중...")
            elif diagnosis_status == 'completed':
                if diagnosis_result and diagnosis_result.get('status') == 'success':
                    risk_level = diagnosis_result.get('risk_level', 'unknown')
                    risk_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    risk_icon = risk_colors.get(risk_level, "⚪")
                    st.write(f"**상태:** ✅ 완료 {risk_icon}")
                else:
                    st.write("**상태:** ❌ 실패")
            
        with col3:
            if diagnosis_status != 'running':
                if st.button("🔍 진단", key=f"diagnose_{item_key}"):
                    # 진단 상태 변경
                    st.session_state[f'diagnosis_status_{item_key}'] = 'running'
                    st.rerun()
            else:
                st.write("🔄 진행중")
        
        # 진단 실행 중일 때 스피너와 함께 실제 진단 수행
        if diagnosis_status == 'running':
            from components.sk_diagnosis import get_checker
            
            from components.aws_handler import AWSConnectionHandler
            aws_handler = st.session_state.get('aws_handler')
            if not aws_handler:
                aws_handler = AWSConnectionHandler()
                st.session_state.aws_handler = aws_handler  # 세션에 저장

            # 연결된 계정 정보로 세션 생성
            account = st.session_state.selected_account
            if account.get('role_arn'):
                # Cross-Account Role 방식
                session = aws_handler.create_session_from_role(
                    role_arn=account['role_arn'],
                    external_id=account.get('external_id'),
                    region=account['primary_region']
                )
            else:
                # Access Key 방식
                session = aws_handler.create_session_from_keys(
                    access_key_id=account['access_key_id'],
                    secret_access_key=account['secret_access_key'],
                    region=account['primary_region']
                )

            checker = get_checker(item['code'])
            if checker:
                # 세션을 체커에 전달
                checker.session = session
                with st.spinner(f"{item['name']}을(를) 분석하고 있습니다..."):
                    result = checker.run_diagnosis()
                    
                    # 결과 저장
                    st.session_state[f'diagnosis_result_{item_key}'] = result
                    st.session_state[f'diagnosis_status_{item_key}'] = 'completed'
                    st.rerun()
            else:
                # 아직 구현되지 않은 항목
                st.session_state[f'diagnosis_result_{item_key}'] = {
                    "status": "not_implemented",
                    "message": f"{item['name']} 진단 기능이 아직 구현되지 않았습니다."
                }
                st.session_state[f'diagnosis_status_{item_key}'] = 'completed'
                st.rerun()
        
        # 진단 완료 후 결과 표시
        if diagnosis_status == 'completed' and diagnosis_result:
            if diagnosis_result.get('status') == 'success':
                show_diagnosis_result(diagnosis_result, item_key, item['code'])
            elif diagnosis_result.get('status') == 'not_implemented':
                st.info(diagnosis_result.get('message', '구현되지 않음'))
            else:
                st.error(f"❌ 진단 실패: {diagnosis_result.get('error_message', '알 수 없는 오류')}")

def show_diagnosis_result(result, item_key, item_code):
    """진단 결과 표시"""
    if item_code == '1.1':
        # 1.1 사용자 계정 관리 결과 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"👑 **관리자:** {result['admin_count']}명")
            if result['admin_users']:
                with st.expander("관리자 목록 보기"):
                    for user in result['admin_users']:
                        st.write(f"• `{user}`")
        
        with col2:
            st.write(f"🧪 **테스트계정:** {result['test_count']}개")
            if result['test_users']:
                with st.expander("테스트계정 목록 보기"):
                    for user in result['test_users']:
                        st.write(f"• `{user}` ⚠️")
        
        # 조치 버튼 (문제가 있는 경우만)
        if result.get('has_issues', False):
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            # 조치 폼 표시
            if st.session_state.get(f'show_fix_{item_key}', False):
                show_fix_form_1_1(result, item_key)
    else:
        # 다른 항목들의 기본 결과 표시
        st.write("📊 진단 결과가 표시됩니다.")

def show_fix_form_1_1(result, item_key):
    """1.1 조치 폼 표시"""
    with st.form(f"fix_form_{item_key}"):
        st.markdown("**🔧 조치할 항목을 선택하세요:**")
        
        selected_admin_users = []
        selected_test_users = []
        
        col1, col2 = st.columns(2)
        
        with col1:
            if result['admin_users']:
                st.markdown("**관리자 권한 제거:**")
                for user in result['admin_users']:
                    if st.checkbox(f"`{user}`", key=f"admin_{item_key}_{user}"):
                        selected_admin_users.append(user)
        
        with col2:
            if result['test_users']:
                st.markdown("**콘솔 로그인 비활성화:**")
                for user in result['test_users']:
                    if st.checkbox(f"`{user}`", key=f"test_{item_key}_{user}"):
                        selected_test_users.append(user)
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            if st.form_submit_button("🚀 조치 실행", type="primary"):
                if selected_admin_users or selected_test_users:
                    execute_fix_1_1(selected_admin_users, selected_test_users, item_key)
                else:
                    st.warning("조치할 항목을 선택해주세요.")
        
        with col_submit2:
            if st.form_submit_button("❌ 취소"):
                st.session_state[f'show_fix_{item_key}'] = False
                st.rerun()

def execute_fix_1_1(selected_admin_users, selected_test_users, item_key):
    """1.1 조치 실행"""
    
    # AWS 세션 다시 생성
    aws_handler = st.session_state.get('aws_handler')
    if not aws_handler:
        aws_handler = AWSConnectionHandler()
        st.session_state.aws_handler = aws_handler  # 세션에 저장
    
    # 연결된 계정 정보로 세션 생성
    account = st.session_state.selected_account
    if account.get('role_arn'):
        # Cross-Account Role 방식
        session = aws_handler.create_session_from_role(
            role_arn=account['role_arn'],
            external_id=account.get('external_id'),
            region=account['primary_region']
        )
    else:
        # Access Key 방식
        session = aws_handler.create_session_from_keys(
            access_key_id=account['access_key_id'],
            secret_access_key=account['secret_access_key'],
            region=account['primary_region']
        )
    
    checker = get_checker('1.1')
    if checker:
        # 세션을 체커에 전달
        checker.session = session
        selected_items = {
            'admin_users': selected_admin_users,
            'test_users': selected_test_users
        }
        
        with st.spinner("조치를 실행하고 있습니다..."):
            results = checker.execute_fix(selected_items)
            
            # 결과 표시
            st.subheader("📊 조치 결과")
            for result in results:
                if result["status"] == "success":
                    st.success(f"✅ {result['user']}: {result['action']} 완료")
                elif result["status"] == "already_done":
                    st.info(f"ℹ️ {result['user']}: 이미 처리됨")
                else:
                    st.error(f"❌ {result['user']}: {result['action']} 실패 - {result.get('error', '알 수 없는 오류')}")
            
            # 재진단 버튼
            if st.button("🔄 재진단", key=f"rediagnose_{item_key}"):
                st.session_state[f'diagnosis_status_{item_key}'] = 'running'
                st.session_state[f'show_fix_{item_key}'] = False
                st.rerun()

def test_session_connection(account):
    """AWS 세션 연결 테스트"""
    try:
        from components.aws_handler import AWSConnectionHandler
        aws_handler = st.session_state.get('aws_handler')
        if not aws_handler:
            aws_handler = AWSConnectionHandler()
            st.session_state.aws_handler = aws_handler  # 세션에 저장
        
        if account.get('role_arn'):
            # Cross-Account Role 테스트
            session = aws_handler.create_session_from_role(
                role_arn=account['role_arn'],
                external_id=account.get('external_id'),
                region=account['primary_region']
            )
            test_message = "Role 세션 생성 성공"
        else:
            # Access Key 방식
            session = aws_handler.create_session_from_keys(
                access_key_id=account['access_key_id'],
                secret_access_key=account['secret_access_key'],
                region=account['primary_region']
            )
            test_message = "Key 세션 생성 성공"
        
        # 간단한 STS 호출로 세션 유효성 확인
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        st.success(f"✅ {test_message}")
        st.write(f"**연결된 계정:** `{identity['Account']}`")
        st.write(f"**사용자 ARN:** `{identity['Arn']}`")
        
    except Exception as e:
        st.error(f"❌ 세션 연결 실패: {str(e)}")

def get_diagnosis_stats():
    """진단 현황 통계 반환"""
    stats = {"idle": 0, "running": 0, "completed": 0, "failed": 0}
    
    for key in st.session_state.keys():
        if key.startswith('diagnosis_status_'):
            status = st.session_state[key]
            if status == 'idle':
                stats['idle'] += 1
            elif status == 'running':
                stats['running'] += 1
            elif status == 'completed':
                result = st.session_state.get(key.replace('status', 'result'))
                if result and result.get('status') == 'success':
                    stats['completed'] += 1
                else:
                    stats['failed'] += 1
    
    return stats

def get_diagnosis_session_info():
    """진단 세션 상세 정보 반환"""
    diagnosis_sessions = {}
    
    for key in st.session_state.keys():
        if key.startswith('diagnosis_status_'):
            item_key = key.replace('diagnosis_status_', '')
            status = st.session_state[key]
            result = st.session_state.get(f'diagnosis_result_{item_key}')
            
            diagnosis_sessions[item_key] = {
                "status": status,
                "has_result": bool(result),
                "result_status": result.get('status') if result else None
            }
    
    return diagnosis_sessions

def clear_diagnosis_states():
    """모든 진단 상태 초기화"""
    keys_to_delete = []
    for key in st.session_state.keys():
        if key.startswith(('diagnosis_status_', 'diagnosis_result_', 'show_fix_')):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]
        
def main():
    """진단 페이지 메인"""
    # 세련된 헤더 렌더링
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
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
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
            background: linear-gradient(45deg, #ffffff, #cbd5e0);
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
                <div class="hero-icon">🔍</div>
                <div class="hero-text">
                    <h1 class="hero-title">AWS 클라우드 보안 IaC 자동 점검</h1>
                    <p class="hero-subtitle">KISA ISMS-P 매핑 31개 + SK Shieldus 2024 가이드라인 10개 항목</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Components로 렌더링
    components.html(header_html, height=200)
    
    # 선택된 계정 정보 확인
    if 'selected_account' not in st.session_state:
        st.error("❌ 선택된 계정이 없습니다. 메인 페이지에서 계정을 선택해주세요.")
        if st.button("🏠 메인으로 돌아가기"):
            st.switch_page("main.py")
        return
    
    account = st.session_state.selected_account
    
    # 사이드바 디버깅 정보
    with st.sidebar:
        st.markdown("### 🔧 진단 디버깅")
        
        # 계정 연결 상태
        st.markdown("#### 📡 연결 상태")
        connection_type = "🛡️ Role" if account.get('role_arn') else "🔑 Key"
        st.write(f"**연결 방식:** {connection_type}")
        st.write(f"**계정 ID:** `{account.get('account_id', 'N/A')}`")
        st.write(f"**리전:** `{account.get('primary_region', 'N/A')}`")
        
        # AWS 핸들러 상태
        aws_handler = st.session_state.get('aws_handler')
        handler_status = "✅ 활성" if aws_handler else "❌ 비활성"
        st.write(f"**AWS Handler:** {handler_status}")
        
        # 진단 세션 테스트
        st.markdown("#### 🧪 세션 테스트")
        if st.button("🔍 세션 연결 테스트", use_container_width=True):
            test_session_connection(account)
        
        # 진행 중인 진단 현황
        st.markdown("#### 📊 진단 현황")
        diagnosis_stats = get_diagnosis_stats()
        st.write(f"**대기중:** {diagnosis_stats['idle']}개")
        st.write(f"**진행중:** {diagnosis_stats['running']}개")
        st.write(f"**완료:** {diagnosis_stats['completed']}개")
        st.write(f"**실패:** {diagnosis_stats['failed']}개")
        
        # 세션 상태 상세 정보
        with st.expander("🐛 상세 디버그 정보"):
            # Secret Key 디버깅 정보 추가
            debug_info = {
            "current_step": "diagnosis",
            "selected_account": account.get('cloud_name', ''),
            "account_id": account.get('account_id', ''),
            "connection_type": "role" if account.get('role_arn') else "access_key",
            "region": account.get('primary_region', ''),
            "secret_key_length": len(account.get('secret_access_key', '')) if account.get('secret_access_key') else 0,
            "diagnosis_sessions": get_diagnosis_session_info()
        }
        st.json(debug_info)
        
        # 진단 세션 초기화
        if st.button("🗑️ 진단 상태 초기화", type="secondary", use_container_width=True):
            from components.session_manager import SessionManager
            SessionManager.clear_diagnosis_states()
            st.success("진단 상태가 초기화되었습니다.")
            st.rerun()
    
    # 계정 정보 표시
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"### ☁️ 대상 계정: {account.get('cloud_name', 'Unknown')}")
        st.write(f"**계정 ID:** `{account.get('account_id', 'N/A')}`")
        
    with col2:
        st.write(f"**리전:** `{account.get('primary_region', 'N/A')}`")
        connection_type = "🛡️ Cross-Account Role" if account.get('role_arn') else "🔑 Access Key"
        st.write(f"**연결 방식:** {connection_type}")
        
    with col3:
        if st.button("🏠 메인으로"):
            st.switch_page("main.py")
    
    st.markdown("---")
    
    # 진단 항목들 표시
    sk_items = get_sk_shieldus_items()
    
    # 전체 통계
    total_items = sum(len(items) for items in sk_items.values())
    st.info(f"📊 **총 {total_items}개** 보안 진단 항목 | 🔴 상위험 13개 | 🟡 중위험 25개 | 🟢 저위험 3개")
    
    # 각 카테고리별 진단 항목 표시
    for category, items in sk_items.items():
        st.subheader(f"📋 {category} ({len(items)}개 항목)")
        
        for index, item in enumerate(items):
            with st.expander(f"{item['code']} {item['name']} {importance_colors.get(item['importance'], '⚪')}"):
                render_diagnosis_item(item, category.replace(' ', '_'), index)
                
        st.markdown("---")
    
    # 하단 액션 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 전체 항목 일괄 진단", type="primary", use_container_width=True):
            st.info("전체 진단 기능 (준비중)")
            
    with col2:
        if st.button("📊 진단 보고서 생성", type="secondary", use_container_width=True):
            st.info("보고서 생성 기능 (준비중)")

if __name__ == "__main__":
    main()