"""
WALB SK Shieldus 41개 항목 보안 진단 페이지
AWS 클라우드 보안 자동화 진단 시스템의 메인 진입점

Functions:
- main(): 진단 페이지 메인 함수 - UI 인스턴스 생성 및 렌더링 오케스트레이션

Page Structure (5파일 구조):
- diagnosis_ui.py: 모든 UI 기능 통합 (페이지+컴포넌트+핸들러)
- diagnosis_engine.py: 비즈니스 로직 (AWS 진단 실행)
- diagnosis_config.py: 데이터 (41개 진단 항목)
- diagnosis_templates.py: HTML 템플릿
- diagnosis_styles.py: CSS 스타일

Features:
- SK Shieldus 2024 가이드라인 기반 41개 보안 진단 항목
- Role ARN/Access Key 방식 AWS 계정 연결 지원
- 개별 진단 및 일괄 진단 기능
- 1열/2열 반응형 레이아웃
- 실시간 진단 진행률 표시
- 자동 조치 실행 기능
"""

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from components.diagnosis_styles import get_all_diagnosis_styles
from components.diagnosis_templates import get_hero_header_html
from components.diagnosis_ui import DiagnosisUI

# 페이지 설정
st.set_page_config(
    page_title="보안 진단 - WALB",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """진단 페이지 메인 함수 - DiagnosisUI 인스턴스 생성 후 단계별 렌더링"""
    # 진단 UI 인스턴스 생성
    ui = DiagnosisUI()
    
    # 계정 선택 확인
    if not ui.check_account_selection():
        return
    
    # CSS 스타일 및 헤더
    st.markdown(get_all_diagnosis_styles(), unsafe_allow_html=True)
    components.html(get_hero_header_html(), height=200)
    
    # 사이드바
    ui.render_sidebar()
    
    # 계정 정보 및 통계
    st.markdown("---")
    st.markdown("### ☁️ 연결된 AWS 계정 정보")
    ui.render_account_info_cards(st.session_state.selected_account)
    st.markdown("---")
    ui.render_statistics_info()
    
    # 메인 컨텐츠
    ui.render_layout_controls()
    ui.handle_diagnosis_completion()
    ui.render_diagnosis_items()
    ui.render_report_button()

if __name__ == "__main__":
    main()