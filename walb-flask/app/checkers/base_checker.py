"""
Flask용 진단 체커 베이스 클래스
mainHub의 BaseChecker를 Streamlit 종속성 제거하여 이식
"""
from abc import ABC, abstractmethod

class BaseChecker(ABC):
    """Flask용 진단 항목 베이스 클래스"""
    
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
    
    def get_result_summary(self, result):
        """
        진단 결과를 Flask 템플릿용 데이터로 변환
        Streamlit UI 렌더링 대신 데이터만 반환
        """
        if result.get('status') != 'success':
            return {
                'status': 'error',
                'error_message': result.get('error_message', '진단 실행 중 오류가 발생했습니다.')
            }
        
        formatted_result = {
            'status': 'success',
            'has_issues': result.get('has_issues', False),
            'risk_level': result.get('risk_level', 'low'),
            'summary': self._format_result_summary(result),
            'details': self._format_result_details(result),
            'fix_options': self._get_fix_options(result) if result.get('has_issues') else None
        }
        
        # 수동 조치 가이드는 보안 이슈가 있을 때만 표시 (다양한 시그니처 지원)
        if result.get('has_issues'):
            try:
                manual_guide = self._get_manual_guide(result)
            except TypeError:
                # 인자를 받지 않는 메서드의 경우
                try:
                    manual_guide = self._get_manual_guide()
                except:
                    manual_guide = None
            except:
                manual_guide = None
                
            if manual_guide:
                formatted_result['manual_guide'] = manual_guide
            
        return formatted_result
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅 - 하위 클래스에서 오버라이드 가능"""
        if result.get('has_issues'):
            return "보안 이슈가 발견되었습니다."
        else:
            return "보안 이슈가 발견되지 않았습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅 - 하위 클래스에서 오버라이드 가능"""
        details = {}
        
        # 기본 결과 정보를 details에 복사 (status, risk_level, has_issues 제외)
        exclude_keys = {'status', 'risk_level', 'has_issues', 'error_message'}
        for key, value in result.items():
            if key not in exclude_keys:
                details[key] = value
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환 - 하위 클래스에서 오버라이드 가능"""
        return None  # 기본적으로 자동 조치 없음
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 하위 클래스에서 오버라이드 가능"""
        return None  # 기본적으로 수동 가이드 없음