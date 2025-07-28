"""
AWS 계정 연결 메인 페이지
4단계 온보딩 프로세스의 간단한 컨트롤러

Functions:
- main: 메인 애플리케이션 함수 - UI 인스턴스 생성 및 단계별 렌더링 오케스트레이션

Page Structure (4파일 구조):
- connection_ui.py: 모든 UI 기능 통합 (페이지+컴포넌트)
- connection_engine.py: 비즈니스 로직 (AWS 연결/테스트/검증)
- connection_config.py: 설정/데이터 (상수, 기본값, 검증 규칙)
- connection_templates.py: HTML 템플릿

Features:
- 4단계 온보딩 프로세스 (방식선택 → 권한설정 → 정보입력 → 연결테스트)
- Cross-Account Role/Access Key 방식 지원
- 실시간 입력 검증 및 AWS 연결 테스트
- IAM 정책 자동 생성 및 표시
- 반응형 UI와 단계별 진행 표시
"""

import streamlit as st
from components.connection_ui import ConnectionUI
from components.connection_styles import get_all_styles
from components.session_manager import SessionManager

# 페이지 설정
st.set_page_config(
    page_title="AWS 계정 연결 - WALB",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """메인 애플리케이션 함수 - UI 인스턴스 생성 후 단계별 렌더링 오케스트레이션"""
    # CSS 스타일 적용
    st.markdown(get_all_styles(), unsafe_allow_html=True)
    
    # 세션 초기화
    SessionManager.initialize_session()
    
    # UI 인스턴스 생성
    ui = ConnectionUI()
    
    # 헤더 렌더링
    ui.render_header()
    
    # 현재 단계에 따른 페이지 렌더링 (안전한 접근)
    current_step = st.session_state.get('current_step', 1)
    
    if current_step == 1:
        ui.render_step1()
    elif current_step == 2:
        ui.render_step2()
    elif current_step == 3:
        ui.render_step3()
    elif current_step == 4:
        ui.render_step4()
    else:
        # 잘못된 단계인 경우 1단계로 리셋
        st.session_state.current_step = 1
        st.rerun()
    
    # 사이드바 렌더링
    ui.render_sidebar()

if __name__ == "__main__":
    main()