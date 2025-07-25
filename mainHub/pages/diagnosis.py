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
from components.diagnosis_ui_handler import DiagnosisUIHandler
from components.connection_styles import get_all_styles 

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
            {"code": "1.1", "name": "사용자 계정 관리", "importance": "상", "description": "AWS 계정의 IAM 사용자들이 적절한 권한과 정책으로 관리되고 있는지, 불필요한 권한이 부여되지 않았는지를 진단합니다."},
            {"code": "1.2", "name": "IAM 사용자 계정 단일화 관리", "importance": "상", "description": "한 명의 사용자가 여러 개의 IAM 계정을 보유하고 있지 않은지, 1인 1계정 원칙이 준수되고 있는지를 점검합니다."},
            {"code": "1.3", "name": "IAM 사용자 계정 식별 관리", "importance": "중", "description": "모든 IAM 사용자에게 이름, 부서, 역할 등의 식별 태그가 적절히 설정되어 있어 사용자를 명확히 구분할 수 있는지 진단합니다."},
            {"code": "1.4", "name": "IAM 그룹 사용자 계정 관리", "importance": "중", "description": "IAM 사용자들이 개별 권한 대신 그룹 기반으로 권한을 관리받고 있는지, 그룹별 권한이 적절히 분리되어 있는지를 점검합니다."},
            {"code": "1.5", "name": "Key Pair 접근 관리", "importance": "상", "description": "실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 패스워드 없이 안전한 SSH 접근이 가능한지를 진단합니다."},
            {"code": "1.6", "name": "Key Pair 보관 관리", "importance": "상", "description": "EC2 Key Pair 파일(.pem)이 공개 접근 가능한 S3 버킷에 저장되어 보안 위험을 초래하지 않는지 점검합니다."},
            {"code": "1.7", "name": "Admin Console 관리자 정책 관리", "importance": "중", "description": "AWS Management Console의 관리자 권한이 필요 이상으로 부여되지 않았는지, 관리자 계정 사용이 적절한지를 진단합니다."},
            {"code": "1.8", "name": "Admin Console 계정 Access Key 활성화 및 사용주기 관리", "importance": "상", "description": "관리자 계정의 Access Key가 장기간 사용되고 있지 않은지, 정기적인 로테이션이 이루어지고 있는지를 점검합니다."},
            {"code": "1.9", "name": "MFA (Multi-Factor Authentication) 설정", "importance": "중", "description": "중요한 IAM 사용자와 루트 계정에 다중 인증(MFA)이 활성화되어 계정 보안이 강화되어 있는지 진단합니다."},
            {"code": "1.10", "name": "AWS 계정 패스워드 정책 관리", "importance": "중", "description": "IAM 계정의 패스워드 정책이 충분히 강력하게 설정되어 있는지, 길이/복잡도/만료 정책이 적절한지를 점검합니다."},
            {"code": "1.11", "name": "EKS 사용자 관리", "importance": "상", "description": "Amazon EKS 클러스터에 접근하는 사용자들의 권한이 적절히 관리되고 있는지, 불필요한 클러스터 접근 권한이 없는지 진단합니다."},
            {"code": "1.12", "name": "EKS 서비스 어카운트 관리", "importance": "중", "description": "EKS 클러스터 내 Kubernetes 서비스 어카운트들이 최소 권한 원칙에 따라 관리되고 있는지를 점검합니다."},
            {"code": "1.13", "name": "EKS 불필요한 익명 접근 관리", "importance": "상", "description": "EKS 클러스터에 익명 사용자의 접근이 허용되어 있지 않은지, 인증되지 않은 접근 경로가 차단되어 있는지 진단합니다."}
        ],
        "권한 관리": [
            {"code": "2.1", "name": "인스턴스 서비스 정책 관리", "importance": "상", "description": "EC2, RDS, S3 등 핵심 AWS 서비스에 대한 IAM 정책이 과도한 권한을 부여하지 않고 최소 권한 원칙을 준수하는지 진단합니다."},
            {"code": "2.2", "name": "네트워크 서비스 정책 관리", "importance": "상", "description": "VPC, Route53, CloudFront 등 네트워크 관련 서비스의 IAM 권한이 적절히 제한되어 있는지, 네트워크 설정 변경 권한이 안전하게 관리되는지 점검합니다."},
            {"code": "2.3", "name": "기타 서비스 정책 관리", "importance": "상", "description": "CloudWatch, CloudTrail, Lambda 등 기타 AWS 서비스들에 대한 권한이 업무 목적에 맞게 최소한으로 부여되어 있는지 진단합니다."}
        ],
        "가상 리소스 관리": [
            {"code": "3.1", "name": "보안 그룹 인/아웃바운드 ANY 설정 관리", "importance": "상", "description": "EC2 보안 그룹에서 모든 포트(0-65535)를 허용하는 위험한 ANY 설정이 사용되고 있지 않은지 점검합니다."},
            {"code": "3.2", "name": "보안 그룹 인/아웃바운드 불필요 정책 관리", "importance": "상", "description": "사용되지 않는 보안 그룹이나 ANY IP(0.0.0.0/0) 규칙을 포함한 불필요한 보안 그룹이 있는지 찾아 정리가 필요한지 진단합니다."},
            {"code": "3.3", "name": "네트워크 ACL 인/아웃바운드 트래픽 정책 관리", "importance": "중", "description": "VPC의 Network ACL에서 과도하게 개방된 트래픽 규칙이 있는지, 필요한 트래픽만 허용하도록 설정되어 있는지 점검합니다."},
            {"code": "3.4", "name": "라우팅 테이블 정책 관리", "importance": "중", "description": "VPC 라우팅 테이블에서 불필요한 라우팅 경로나 보안상 위험한 라우팅 설정이 있는지, 프라이빗 서브넷의 격리가 적절한지 진단합니다."},
            {"code": "3.5", "name": "인터넷 게이트웨이 연결 관리", "importance": "하", "description": "인터넷 게이트웨이가 필요하지 않은 VPC나 서브넷에 연결되어 있지 않은지, IGW 연결 상태가 보안 정책에 부합하는지 점검합니다."},
            {"code": "3.6", "name": "NAT 게이트웨이 연결 관리", "importance": "중", "description": "프라이빗 서브넷의 아웃바운드 인터넷 접근을 위한 NAT Gateway 설정이 적절한지, 불필요한 NAT 연결이 없는지 진단합니다."},
            {"code": "3.7", "name": "S3 버킷/객체 접근 관리", "importance": "중", "description": "S3 버킷이 의도치 않게 퍼블릭으로 노출되어 있지 않은지, 버킷 정책과 ACL이 적절히 설정되어 데이터가 안전한지 점검합니다."},
            {"code": "3.8", "name": "RDS 서브넷 가용 영역 관리", "importance": "중", "description": "RDS 인스턴스가 적절한 서브넷 그룹에 배치되어 있는지, 다중 AZ 구성으로 고가용성이 확보되어 있는지 진단합니다."},
            {"code": "3.9", "name": "EKS Pod 보안 정책 관리", "importance": "상", "description": "EKS 클러스터에서 Pod Security Standards가 적용되어 있는지, 컨테이너 실행 권한이 적절히 제한되어 있는지 점검합니다."},
            {"code": "3.10", "name": "ELB(Elastic Load Balancing) 연결 관리", "importance": "중", "description": "로드밸런서의 리스너 설정과 보안 그룹이 적절한지, SSL/TLS 설정이 안전하게 구성되어 있는지 진단합니다."}
        ],
        "운영 관리": [
            {"code": "4.1", "name": "EBS 및 볼륨 암호화 설정", "importance": "중", "description": "EC2 인스턴스의 EBS 볼륨과 스냅샷이 암호화되어 저장되고 있는지, 데이터 유출 시 보호가 가능한지 점검합니다."},
            {"code": "4.2", "name": "RDS 암호화 설정", "importance": "중", "description": "RDS 데이터베이스 인스턴스의 저장 데이터와 백업이 암호화되어 있는지, 전송 중 암호화도 적용되어 있는지 진단합니다."},
            {"code": "4.3", "name": "S3 암호화 설정", "importance": "중", "description": "S3 버킷에 기본 암호화가 활성화되어 있는지, 업로드되는 모든 객체가 자동으로 암호화되도록 설정되어 있는지 점검합니다."},
            {"code": "4.4", "name": "통신구간 암호화 설정", "importance": "중", "description": "AWS 서비스 간 통신과 클라이언트-서버 간 데이터 전송이 TLS/SSL로 암호화되어 있는지, HTTPS 사용이 강제되는지 진단합니다."},
            {"code": "4.5", "name": "CloudTrail 암호화 설정", "importance": "중", "description": "AWS CloudTrail 로그가 KMS 키로 암호화되어 저장되고 있는지, 감사 로그의 무결성이 보장되는지 점검합니다."},
            {"code": "4.6", "name": "CloudWatch 암호화 설정", "importance": "중", "description": "CloudWatch 로그 그룹이 KMS 암호화로 보호되고 있는지, 모니터링 데이터가 안전하게 저장되는지 진단합니다."},
            {"code": "4.7", "name": "AWS 사용자 계정 로깅 설정", "importance": "상", "description": "IAM 사용자들의 모든 활동이 CloudTrail을 통해 기록되고 있는지, 계정 사용 내역을 추적할 수 있는지 점검합니다."},
            {"code": "4.8", "name": "인스턴스 로깅 설정", "importance": "중", "description": "EC2 인스턴스의 시스템 로그와 애플리케이션 로그가 CloudWatch나 중앙 로깅 시스템으로 수집되고 있는지 진단합니다."},
            {"code": "4.9", "name": "RDS 로깅 설정", "importance": "중", "description": "RDS 데이터베이스의 쿼리 로그, 에러 로그, 슬로우 쿼리 로그가 활성화되어 데이터베이스 활동을 모니터링할 수 있는지 점검합니다."},
            {"code": "4.10", "name": "S3 버킷 로깅 설정", "importance": "중", "description": "S3 버킷에 액세스 로깅이 활성화되어 있는지, 버킷에 대한 모든 요청이 기록되어 추적 가능한지 진단합니다."},
            {"code": "4.11", "name": "VPC 플로우 로깅 설정", "importance": "중", "description": "VPC Flow Logs가 활성화되어 네트워크 트래픽이 기록되고 있는지, 네트워크 보안 분석이 가능한지 점검합니다."},
            {"code": "4.12", "name": "로그 보관 기간 설정", "importance": "중", "description": "각종 로그들의 보존 기간이 규정에 맞게 설정되어 있는지, 비용 효율적이면서도 규정을 준수하는지 진단합니다."},
            {"code": "4.13", "name": "백업 사용 여부", "importance": "중", "description": "중요한 데이터와 시스템에 대한 백업 정책이 수립되어 있는지, 자동 백업이 정상적으로 수행되고 있는지 점검합니다."},
            {"code": "4.14", "name": "EKS Cluster 제어 플레인 로깅 설정", "importance": "중", "description": "EKS 클러스터의 API 서버, 감사, 인증 등 제어 플레인 로그가 CloudWatch로 전송되어 기록되고 있는지 진단합니다."},
            {"code": "4.15", "name": "EKS Cluster 암호화 설정", "importance": "중", "description": "EKS 클러스터의 etcd에 저장되는 Kubernetes Secret이 KMS 키로 암호화되어 있는지, 클러스터 데이터가 안전한지 점검합니다."}
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

# 글로벌 UI 핸들러 인스턴스
ui_handler = DiagnosisUIHandler()

def render_diagnosis_item(item, category, index):
    """진단 항목 카드 렌더링 - 대폭 간소화"""
    importance_color = importance_colors.get(item["importance"], "⚪")
    item_key = f"{category}_{index}"
    
    # 진단 실행 중인 항목에 대한 자동 스크롤을 위한 고유 ID 생성
    container_id = f"diagnosis_item_{item_key}"
    
    with st.container():
        # 이 컨테이너만 여백 줄이기 (매우 작게)
        st.markdown(f"""
        <style>
        div[data-testid="stVerticalBlock"]:has(#{container_id}) {{
            padding-top: 0.05rem !important;
            margin-top: 0.05rem !important;
        }}
        div[data-testid="stExpanderDetails"] {{
            padding-top: 0 !important;
        }}
        div[data-testid="stVerticalBlock"][height="90%"] {{
            margin-top: 8px !important;
        }}
        div[data-testid="stVerticalBlock"][height="100%"] {{
            gap: 0.3rem !important;
        }}
        div[data-testid="stVerticalBlock"][height="100%"] > div {{
            margin-bottom: 0.2rem !important;
        }}
        /* 1열 레이아웃에서도 항목 간 여백 더 줄이기 */
        .stExpander {{
            margin-bottom: 0.1rem !important;
        }}
        .stExpander + .stExpander {{
            margin-top: 0.05rem !important;
        }}
        /* 매트릭 박스 스타일 개선 */
        div[data-testid="metric-container"] {{
            background-color: #f8f9fa !important;
            border: 1px solid #e9ecef !important;
            border-radius: 8px !important;
            padding: 12px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }}
        div[data-testid="metric-container"] > div:first-child {{
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            color: #6c757d !important;
            margin-bottom: 4px !important;
        }}
        div[data-testid="metric-container"] > div:last-child {{
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: #212529 !important;
        }}
        /* 매트릭 박스 제목 전체 스타일 */
        h3:has(+ div div[data-testid="metric-container"]) {{
            font-size: 1.2rem !important;
            margin-bottom: 1rem !important;
        }}
        /* Expander 제목 스타일링 - 일관된 너비 */
        .streamlit-expanderHeader {{
            font-family: 'Courier New', monospace !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        diagnosis_status = st.session_state.get(f'diagnosis_status_{item_key}', 'idle')
        diagnosis_result = st.session_state.get(f'diagnosis_result_{item_key}', None)
        
        # 진단 항목 카드 디자인 개선
        card_style = """
        <style>
        .diagnosis-card {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .diagnosis-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 8px;
        }
        .diagnosis-description {
            color: #4a5568;
            font-size: 0.9rem;
            margin-bottom: 12px;
        }
        .diagnosis-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 12px;
        }
        .importance-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .diagnosis-button {
            width: 100%;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            font-weight: 500;
            cursor: pointer;
        }
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        
        # 상태별 스타일
        if diagnosis_status == 'idle':
            status_text = "⏳ 대기중"
            status_color = "#718096"
        elif diagnosis_status == 'running':
            status_text = "🔄 진단중..."
            status_color = "#3182ce"
        elif diagnosis_status == 'completed':
            if diagnosis_result and diagnosis_result.get('status') == 'success':
                risk_level = diagnosis_result.get('risk_level', 'unknown')
                risk_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                risk_icon = risk_colors.get(risk_level, "⚪")
                status_text = f"✅ 완료 {risk_icon}"
                status_color = "#38a169"
            else:
                status_text = "❌ 실패"
                status_color = "#e53e3e"
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="diagnosis-card">
                <div class="diagnosis-header">{item['code']} {item['name']}</div>
                <div class="diagnosis-description">📝 {item['description']}</div>
                <div class="diagnosis-meta">
                    <span><strong>중요도:</strong> {importance_color} {item['importance']}</span>
                    <span><strong>상태:</strong> <span style="color: {status_color};">{status_text}</span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            # 진단 버튼 (항상 표시)
            if diagnosis_status != 'running':
                if st.button("🔍 진단", key=f"diagnose_{item_key}", use_container_width=True):
                    st.session_state[f'diagnosis_status_{item_key}'] = 'running'
                    st.rerun()
            else:
                st.markdown("""
                <div style="text-align: center; padding: 8px;">
                    <div style="color: #3182ce; font-weight: 500;">🔄 진행중</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 진단 완료 후 위험도 표시 (진단 버튼 아래에 추가)
            if diagnosis_status == 'completed' and diagnosis_result:
                risk_level = diagnosis_result.get('risk_level', 'unknown')
                if risk_level != 'unknown':
                    risk_colors = {
                        "high": ("🔴", "#e53e3e", "높음"),
                        "medium": ("🟡", "#dd6b20", "보통"), 
                        "low": ("🟢", "#38a169", "낮음")
                    }
                    
                    if risk_level in risk_colors:
                        icon, color, text = risk_colors[risk_level]
                        st.markdown(f"""
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: 6px 12px;
                            background-color: {color}15;
                            border: 1px solid {color}40;
                            border-radius: 6px;
                            font-size: 0.9rem;
                            margin-top: 8px;
                            box-sizing: border-box;
                        ">
                            <span style="margin-right: 4px; font-size: 1rem;">{icon}</span>
                            <span style="font-weight: 600; color: {color};">{text}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # risk_level이 없는 경우 기본 완료 표시
                    st.markdown("""
                    <div style="
                        text-align: center; 
                        padding: 4px 8px;
                        margin-top: 8px;
                        color: #38a169; 
                        font-weight: 500;
                        font-size: 0.9rem;
                    ">✅ 완료</div>
                    """, unsafe_allow_html=True)
        
        # 진단 실행 - 단일 중앙 정렬 스피너
        if diagnosis_status == 'running':
            # 자동 스크롤을 위한 보이지 않는 마커 (항목 정보와 스피너 사이에 배치)
            if st.session_state.get('full_diagnosis_running', False):
                scroll_script = f"""
                <div id="{container_id}" style="position: absolute; height: 0; width: 0; visibility: hidden;"></div>
                <script>
                setTimeout(function() {{
                    var element = document.getElementById('{container_id}');
                    if (element) {{
                        element.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'center',
                            inline: 'nearest'
                        }});
                    }}
                }}, 500);
                </script>
                """
                components.html(scroll_script, height=0)
            
            # 중앙 정렬된 진단 진행 표시
            st.markdown("""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px;
                margin: 16px 0;
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            ">
                <div style="
                    font-size: 2rem;
                    animation: spin 2s linear infinite;
                    margin-bottom: 12px;
                ">🔍</div>
                <div style="
                    font-size: 1.1rem;
                    font-weight: 600;
                    color: #2d3748;
                    text-align: center;
                ">진단 진행 중...</div>
                <div style="
                    font-size: 0.9rem;
                    color: #4a5568;
                    text-align: center;
                    margin-top: 4px;
                ">{} 분석 중</div>
            </div>
            <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            </style>
            """.format(item['name']), unsafe_allow_html=True)
            
            # 실제 진단 실행 (백그라운드 처리)
            result = ui_handler.run_diagnosis(item['code'], item['name'])
            st.session_state[f'diagnosis_result_{item_key}'] = result
            st.session_state[f'diagnosis_status_{item_key}'] = 'completed'
            st.rerun()
        
        # 진단 결과 표시
        if diagnosis_status == 'completed' and diagnosis_result:
            # 설명과 결과 사이에 구분선 추가
            st.markdown("---")
            
            if diagnosis_result.get('status') == 'success':
                ui_handler.show_diagnosis_result(diagnosis_result, item_key, item['code'])
                
                # 조치 폼 표시 (show_fix_{item_key} 상태가 True일 때)
                if st.session_state.get(f'show_fix_{item_key}', False):
                    st.markdown("---")
                    ui_handler.show_fix_form(diagnosis_result, item_key, item['code'])
                    
            elif diagnosis_result.get('status') == 'not_implemented':
                st.info(diagnosis_result.get('message', '구현되지 않음'))
            else:
                st.error(f"❌ 진단 실패: {diagnosis_result.get('error_message', '알 수 없는 오류')}")
        
        # 컨테이너 div 닫기
        st.markdown('</div>', unsafe_allow_html=True)
                
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

def run_full_diagnosis():
    """전체 41개 항목 일괄 진단 실행"""
    st.session_state['full_diagnosis_running'] = True
    
    # 모든 진단 항목에 대해 진단 상태를 'running'으로 설정
    sk_items = get_sk_shieldus_items()
    
    total_items = 0
    for category, items in sk_items.items():
        category_key = category.replace(' ', '_')
        for index, item in enumerate(items):
            item_key = f"{category_key}_{index}"
            st.session_state[f'diagnosis_status_{item_key}'] = 'running'
            total_items += 1
    
    st.success(f"🚀 {total_items}개 항목의 전체 진단을 시작합니다!")
    
    # 모든 expander를 열어놓기 위한 플래그 설정
    st.session_state['expand_all_items'] = True
        
def main():
    # CSS 스타일 주입
    st.markdown(get_all_styles(), unsafe_allow_html=True)
    
    # 스크롤 관련 CSS 추가
    st.markdown("""
    <style>
    .scroll-target {
        scroll-margin-top: 100px;
    }
    
    /* 특정 영역의 위쪽 여백 줄이기 - 안정적인 셀렉터 사용 */
    div[data-testid="stMainBlockContainer"] > div > div:nth-child(13) > div > details > div > div > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* 더 넓은 범위로 진단 항목들의 상단 여백 줄이기 */
    div[data-testid="stExpanderDetails"] > div > div {
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
        
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
        # 전체 진단 진행 상태를 사이드바에 표시
        if st.session_state.get('full_diagnosis_running', False):
            st.markdown("### 🚀 전체 진단 진행 중")
            
            # 진행률 계산
            diagnosis_stats = get_diagnosis_stats()
            total_items = diagnosis_stats['idle'] + diagnosis_stats['running'] + diagnosis_stats['completed'] + diagnosis_stats['failed']
            completed_items = diagnosis_stats['completed'] + diagnosis_stats['failed']
            
            if total_items > 0:
                progress = completed_items / total_items
                st.progress(progress)
                st.write(f"**진행률:** {completed_items}/{total_items} ({progress*100:.1f}%)")
                
                # 현재 진행 중인 항목 표시
                if diagnosis_stats['running'] > 0:
                    st.write(f"🔄 **진행 중:** {diagnosis_stats['running']}개")
                    
                    # 현재 실행 중인 항목들 찾기
                    running_items = []
                    sk_items = get_sk_shieldus_items()
                    for category, items in sk_items.items():
                        category_key = category.replace(' ', '_')
                        for index, item in enumerate(items):
                            item_key = f"{category_key}_{index}"
                            if st.session_state.get(f'diagnosis_status_{item_key}') == 'running':
                                running_items.append(f"{item['code']} {item['name']}")
                    
                    if running_items:
                        st.markdown("**현재 실행 중:**")
                        for item in running_items[:3]:  # 최대 3개만 표시
                            st.write(f"• {item}")
                        if len(running_items) > 3:
                            st.write(f"• ... 외 {len(running_items)-3}개")
            
            st.divider()
        
        # 진단 관리 (진단 완료 후에만 표시)
        if not st.session_state.get('full_diagnosis_running', False):
            st.markdown("### 🎛️ 진단 관리")
            
            # 토글박스 상태에 따라 버튼 텍스트 변경
            if st.session_state.get('expand_all_items', False):
                if st.button("📁 모든 항목 접기", type="secondary", use_container_width=True):
                    st.session_state['expand_all_items'] = False
                    st.rerun()
            else:
                if st.button("📂 모든 항목 펼치기", type="secondary", use_container_width=True):
                    st.session_state['expand_all_items'] = True
                    st.rerun()
            
            # 진단 결과 초기화
            if st.button("🗑️ 모든 진단 결과 초기화", type="secondary", use_container_width=True):
                clear_diagnosis_states()
                st.session_state['full_diagnosis_running'] = False
                st.session_state['expand_all_items'] = False
                st.success("모든 진단 결과가 초기화되었습니다.")
                st.rerun()
            
            st.divider()
        
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
    
    # 계정 정보 표시 - 스트림릿 컴포넌트 사용
    st.markdown("---")
    
    # 계정 정보를 커스텀 스타일로 예쁘게 표시
    st.markdown("### ☁️ 연결된 AWS 계정 정보")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <div style="font-size: 0.7rem; opacity: 0.8; margin-bottom: 4px;">계정 이름</div>
            <div style="font-size: 1.1rem; font-weight: bold;">{account.get('cloud_name', 'Unknown')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 0.7rem; color: #6c757d; margin-bottom: 4px;">계정 ID</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #495057;">{account.get('account_id', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 0.7rem; color: #6c757d; margin-bottom: 4px;">리전</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #495057;">{account.get('primary_region', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        connection_type = "Role 인증" if account.get('role_arn') else "Access Key"
        connection_icon = "🛡️" if account.get('role_arn') else "🔑"
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 0.7rem; color: #6c757d; margin-bottom: 4px;">연결 방식</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #495057;">{connection_icon} {connection_type}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 16px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 0.7rem; color: #6c757d; margin-bottom: 4px;">담당자</div>
            <div style="font-size: 0.9rem; font-weight: 600; color: #495057;">{account.get('contact_email', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 진단 항목들 표시
    sk_items = get_sk_shieldus_items()
    
    # 전체 통계
    total_items = sum(len(items) for items in sk_items.values())
    st.info(f"📊 **총 {total_items}개** 보안 진단 항목 | 🔴 상위험 13개 | 🟡 중위험 25개 | 🟢 저위험 3개")
    
    # 레이아웃 선택 및 전체 진단 버튼
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚀 전체 항목 일괄 진단", type="primary", use_container_width=True):
            run_full_diagnosis()
            st.rerun()
    
    with col2:
        # 전체 진단 중일 때는 레이아웃 변경 비활성화
        layout_disabled = st.session_state.get('full_diagnosis_running', False)
        
        if 'layout_mode' not in st.session_state:
            st.session_state.layout_mode = '2열'
        
        # 레이아웃 선택을 한 줄로 표시하기 위한 스타일
        st.markdown("""
        <style>
        div[data-testid="stRadio"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 38px !important;
        }
        div[data-testid="stRadio"] > label {
            display: flex !important;
            align-items: center !important;
            margin-bottom: 0 !important;
            margin-right: 20px !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }
        div[data-testid="stRadio"] > div {
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
            gap: 20px !important;
        }
        div[data-testid="stRadio"] > div > label {
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
            margin: 0 !important;
            font-weight: 500 !important;
            font-size: 1.05rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        layout_mode = st.radio(
            "📊 레이아웃 선택",
            ["1열", "2열"],
            index=1 if st.session_state.layout_mode == '2열' else 0,
            disabled=layout_disabled,
            help="전체 진단 중에는 레이아웃을 변경할 수 없습니다." if layout_disabled else None,
            horizontal=True
        )
        st.session_state.layout_mode = layout_mode
    
    # 전체 진단 완료 확인
    if st.session_state.get('full_diagnosis_running', False):
        diagnosis_stats = get_diagnosis_stats()
        total_items = diagnosis_stats['idle'] + diagnosis_stats['running'] + diagnosis_stats['completed'] + diagnosis_stats['failed']
        completed_items = diagnosis_stats['completed'] + diagnosis_stats['failed']
        
        # 모든 진단이 완료되면 플래그 해제 (expand_all_items는 유지)
        if total_items > 0 and completed_items == total_items:
            st.session_state['full_diagnosis_running'] = False
            st.session_state['diagnosis_completed'] = True
            st.success("🎉 전체 진단이 완료되었습니다!")
            st.rerun()
    
    # 진단 완료 후 자동 스크롤
    if st.session_state.get('diagnosis_completed', False):
        scroll_script = """
        <script>
        setTimeout(function() {
            window.scrollTo({
                top: 300,
                behavior: 'smooth'
            });
        }, 500);
        </script>
        """
        components.html(scroll_script, height=0)
        # 한 번만 실행하도록 플래그 제거
        st.session_state['diagnosis_completed'] = False
    
    
    # 각 카테고리별 진단 항목 표시 (선택된 레이아웃에 따라)
    categories = list(sk_items.items())
    
    def render_category_items(category, items, category_key):
        """카테고리 항목들을 렌더링하는 헬퍼 함수"""
        st.subheader(f"📋 {category} ({len(items)}개 항목)")
        
        for index, item in enumerate(items):
            expanded = st.session_state.get('expand_all_items', False)
            
            # 일관된 너비로 정렬된 expander 제목
            code_text = item['code']  
            name_text = item['name']
            importance_part = f"{importance_colors.get(item['importance'], '⚪')} {item['importance']}"
            
            # 한글 문자 길이 계산하여 고정폭 정렬
            name_display_length = sum(2 if ord(c) > 127 else 1 for c in name_text)
            spaces_needed = max(0, 35 - name_display_length)
            name_padded = name_text + " " * spaces_needed
            
            with st.expander(f"**{code_text}** | {name_padded} | {importance_part}", expanded=expanded):
                render_diagnosis_item(item, category_key, index)
    
    # 선택된 레이아웃 모드에 따라 렌더링
    if layout_mode == '1열':
        # 1열 레이아웃: 각 카테고리를 순차적으로 표시
        for category, items in categories:
            render_category_items(category, items, category.replace(' ', '_'))
            st.markdown("---")
    
    else:  # 2열 레이아웃
        # 1행: 계정 관리 vs 권한 관리 + 가상 리소스 관리
        col1, col2 = st.columns(2)
        
        with col1:
            # 1번 - 계정 관리 (13개)
            render_category_items(categories[0][0], categories[0][1], categories[0][0].replace(' ', '_'))
        
        with col2:
            # 2번 - 권한 관리 (3개)
            render_category_items(categories[1][0], categories[1][1], categories[1][0].replace(' ', '_'))
            
            # 3번 - 가상 리소스 관리 (10개)  
            render_category_items(categories[2][0], categories[2][1], categories[2][0].replace(' ', '_'))
        
        st.markdown("---")
        
        # 2행: 운영 관리를 절반씩 나누어 2열 배치
        if len(categories) > 3:
            category_name, operation_items = categories[3]  # 운영 관리
            half = len(operation_items) // 2
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📋 {category_name} (1-{half}) ({half}개 항목)")
                for index, item in enumerate(operation_items[:half]):
                    expanded = st.session_state.get('expand_all_items', False)
                    
                    code_text = item['code']  
                    name_text = item['name']
                    importance_part = f"{importance_colors.get(item['importance'], '⚪')} {item['importance']}"
                    
                    name_display_length = sum(2 if ord(c) > 127 else 1 for c in name_text)
                    spaces_needed = max(0, 35 - name_display_length)
                    name_padded = name_text + " " * spaces_needed
                    
                    with st.expander(f"**{code_text}** | {name_padded} | {importance_part}", expanded=expanded):
                        render_diagnosis_item(item, category_name.replace(' ', '_'), index)
            
            with col2:
                remaining = len(operation_items) - half
                st.subheader(f"📋 {category_name} ({half+1}-{len(operation_items)}) ({remaining}개 항목)")
                for index, item in enumerate(operation_items[half:], start=half):
                    expanded = st.session_state.get('expand_all_items', False)
                    
                    code_text = item['code']  
                    name_text = item['name']
                    importance_part = f"{importance_colors.get(item['importance'], '⚪')} {item['importance']}"
                    
                    name_display_length = sum(2 if ord(c) > 127 else 1 for c in name_text)
                    spaces_needed = max(0, 35 - name_display_length)
                    name_padded = name_text + " " * spaces_needed
                    
                    with st.expander(f"**{code_text}** | {name_padded} | {importance_part}", expanded=expanded):
                        render_diagnosis_item(item, category_name.replace(' ', '_'), index)
    
    # 보고서 생성 버튼만 유지
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📊 진단 보고서 생성", type="primary", use_container_width=True):
            st.info("보고서 생성 기능 (준비중)")

if __name__ == "__main__":
    main()