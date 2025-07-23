"""
SK Shieldus 진단 항목 공통 베이스 클래스
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