"""
SK Shieldus 진단 항목 공통 베이스 클래스
"""
from abc import ABC, abstractmethod
import streamlit as st

class BaseChecker(ABC):
    """진단 항목 베이스 클래스"""
    
    def __init__(self, session=None):
        self.session = session
        
    @abstractmethod
    def run_diagnosis(self):
        """진단 수행 - 반드시 구현해야 함"""
        pass
    
    @abstractmethod
    def execute_fix(self, selected_items):
        """조치 실행 - 반드시 구현해야 함"""
        pass
    
    @property
    @abstractmethod
    def item_code(self):
        """항목 코드 (예: 1.1)"""
        pass
    
    @property 
    @abstractmethod
    def item_name(self):
        """항목명"""
        pass
    
    def calculate_risk_level(self, issues_count, severity_score=1):
        """위험도 계산 공통 로직"""
        if issues_count == 0:
            return "low"
        elif issues_count * severity_score > 5:
            return "high"
        else:
            return "medium"
    
    def render_result_ui(self, result, item_key, ui_handler):
        """진단 결과 UI 렌더링 (선택적 구현)"""
        # 기본 구현 - 하위 클래스에서 오버라이드 가능
        ui_handler._show_default_result(result, item_key, self.item_code)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """조치 폼 UI 렌더링 (선택적 구현)"""
        # 기본 구현 - 하위 클래스에서 오버라이드 가능
        st.info("조치 기능이 구현되지 않았습니다.")