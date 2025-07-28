"""
SK Shieldus 진단 항목 공통 베이스 클래스 - Flask 버전
"""
from abc import ABC, abstractmethod

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
    
    def render_result_ui(self, result):
        """진단 결과 UI 렌더링 (선택적 구현) - Flask 버전"""
        # Flask에서는 딕셔너리로 반환하여 템플릿에서 렌더링
        return {
            'item_code': self.item_code,
            'item_name': self.item_name,
            'result': result,
            'ui_type': 'default'
        }
    
    def render_fix_form(self, result):
        """조치 폼 UI 렌더링 (선택적 구현) - Flask 버전"""
        # Flask에서는 딕셔너리로 반환하여 템플릿에서 렌더링
        return {
            'item_code': self.item_code,
            'item_name': self.item_name,
            'message': '조치 기능이 구현되지 않았습니다.',
            'ui_type': 'info'
        }