import json
import os
from datetime import datetime
import streamlit as st

def load_connected_accounts():
    """연결된 AWS 계정 목록 로드 (JSON 파일에서)"""
    accounts = []
    if os.path.exists("registered_accounts.json"):
        try:
            with open("registered_accounts.json", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        account = json.loads(line.strip())
                        accounts.append(account)
        except Exception as e:
            st.error(f"계정 데이터 로드 오류: {str(e)}")
    
    # 중복 제거 (account_id + cloud_name 조합으로)
    seen = set()
    unique_accounts = []
    for account in accounts:
        key = f"{account.get('account_id', '')}_{account.get('cloud_name', '')}"
        if key not in seen:
            seen.add(key)
            unique_accounts.append(account)
    
    return unique_accounts

def render_account_card(account, index):
    """계정 카드 렌더링"""
    connection_type = "🛡️ Cross-Account Role" if account.get('role_arn') else "🔑 Access Key"
    
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"### ☁️ {account.get('cloud_name', 'Unknown')}")
            st.write(f"**계정 ID:** `{account.get('account_id', 'N/A')}`")
            st.write(f"**연결 방식:** {connection_type}")
            st.write(f"**리전:** `{account.get('primary_region', 'N/A')}`")
            
        with col2:
            st.write(f"**담당자:** {account.get('contact_email', 'N/A')}")
            # 연결 상태 (실제 DB 연동 시 상태 필드 추가 필요)
            st.success("🟢 연결됨")
            
        with col3:
            if st.button("📡 모니터링", key=f"monitor_{index}"):
                st.info("모니터링 기능 (준비중)")
            if st.button("🛡️ 항목진단", key=f"diagnosis_{index}"):
                # 선택된 계정 정보를 세션에 저장
                st.session_state.selected_account = account
                st.switch_page("pages/diagnosis.py")

def main():
    """메인 대시보드"""
    st.title("🛡️ WALB - 통합 보안 관리 플랫폼")
    st.markdown("---")
    
    # 연결된 계정 섹션
    st.subheader("☁️ 연결된 AWS 계정")
    
    # 계정 로드
    accounts = load_connected_accounts()
    
    if accounts:
        st.info(f"총 **{len(accounts)}개**의 AWS 계정이 연결되어 있습니다.")
        
        # 계정 카드들 표시
        for index, account in enumerate(accounts):
            with st.expander(f"☁️ {account.get('cloud_name', 'Unknown')} ({account.get('account_id', 'N/A')})"):
                render_account_card(account, index)
                
        # 액션 버튼들
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 새로고침", type="secondary"):
                st.rerun()
                
        with col2:
            if st.button("➕ 계정 추가", type="primary"):
                st.switch_page("pages/connection.py")
                
    else:
        st.warning("연결된 AWS 계정이 없습니다.")
        st.markdown("### 🚀 시작하기")
        st.write("WALB 보안 관리를 시작하려면 AWS 계정을 먼저 연결해주세요.")
        
        if st.button("➕ 첫 번째 계정 연결", type="primary", use_container_width=True):
            st.switch_page("pages/connection.py")
    
    # 구분선
    st.markdown("---")
    
    # 안전한 클라우드 구축 (별도 기능)
    st.subheader("🏗️ 안전한 클라우드 구축")
    st.markdown("""
    **Shift-Left Security 적용** - 사전 보안이 내장된 새로운 AWS 환경을 자동 구축합니다.
    - 🛡️ 사전 보안 내장 인프라
    - 📋 IaC 기반 Terraform 템플릿  
    - ✅ ISMS-P 컴플라이언스 자동 적용
    """)
    
    if st.button("🚀 새 환경 구축 시작", type="primary", use_container_width=True):
        st.info("안전한 클라우드 구축 기능 (준비중)")
        
if __name__ == "__main__":
    main()