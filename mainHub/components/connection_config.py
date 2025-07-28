"""
WALB Connection 설정 및 데이터 관리 모듈
모든 Connection 관련 상수, 기본값, 설정을 중앙 집중 관리

Classes:
- ConnectionConfig: Connection 설정 관리 클래스

Functions:
- get_step_definitions: 4단계 진행 정보 반환
- get_connection_types: 연결 방식 정보 반환
- get_available_regions: AWS 리전 목록 반환
- get_test_services: 테스트할 AWS 서비스 목록 반환
- get_validation_rules: 입력값 검증 규칙 반환
- get_default_session_state: 기본 세션 상태 반환
"""

from typing import Dict, List, Any

def get_step_definitions() -> List[Dict[str, Any]]:
    """4단계 진행 정보 반환"""
    return [
        {"number": 1, "title": "연결 방식 선택"},
        {"number": 2, "title": "권한 설정"},
        {"number": 3, "title": "연결 정보 입력"},
        {"number": 4, "title": "연결 테스트"}
    ]

def get_connection_types() -> Dict[str, Dict[str, str]]:
    """연결 방식 정보 반환"""
    return {
        "cross-account-role": {
            "title": "Cross-Account Role",
            "subtitle": "권장 보안 방식",
            "description": "IAM Role을 통한 안전한 연결",
            "security_level": "높음",
            "icon": "🛡️"
        },
        "access-key": {
            "title": "Access Key",
            "subtitle": "간편 연결 방식",
            "description": "Access Key를 통한 직접 연결",
            "security_level": "보통",
            "icon": "🔑"
        }
    }

def get_available_regions() -> Dict[str, str]:
    """AWS 리전 목록과 표시명 매핑 반환"""
    return {
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'us-east-1': 'US East (N. Virginia)',
        'us-west-2': 'US West (Oregon)',
        'eu-west-1': 'Europe (Ireland)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'eu-central-1': 'Europe (Frankfurt)',
        'us-west-1': 'US West (N. California)',
        'ap-south-1': 'Asia Pacific (Mumbai)'
    }

def get_test_services() -> List[str]:
    """테스트할 AWS 서비스 목록 반환"""
    return [
        'ec2', 's3', 'iam', 'cloudtrail', 
        'cloudwatch', 'rds', 'eks'
    ]

def get_validation_rules() -> Dict[str, Any]:
    """입력값 검증 규칙 반환"""
    return {
        'account_id': {
            'length': 12,
            'pattern': r'^\d{12}$',
            'error_message': '12자리 숫자여야 합니다'
        },
        'access_key': {
            'min_length': 16,
            'max_length': 32,
            'pattern': r'^[A-Z0-9]+$',
            'error_message': '16-32자리 대문자 영숫자여야 합니다'
        },
        'secret_key': {
            'min_length': 28,
            'max_length': 50,
            'pattern': r'^[A-Za-z0-9+/]+$',
            'error_message': '28-50자리 Base64 형식이어야 합니다'
        },
        'role_arn': {
            'pattern': r'^arn:aws:iam::\d{12}:role/[a-zA-Z0-9+=,.@_-]+$',
            'error_message': '올바른 IAM Role ARN 형식이어야 합니다'
        },
        'email': {
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'error_message': '올바른 이메일 형식이어야 합니다'
        }
    }

def get_default_session_state() -> Dict[str, Any]:
    """기본 세션 상태 반환"""
    return {
        'current_step': 1,
        'connection_type': 'cross-account-role',
        'account_data': {
            'cloud_name': '',
            'account_id': '',
            'role_arn': '',
            'external_id': '',
            'access_key_id': '',
            'secret_access_key': '',
            'primary_region': 'ap-northeast-2',
            'contact_email': ''
        },
        'connection_status': 'idle',
        'test_results': None,
        'security_warnings': [],
        'initialized_at': None
    }

def get_info_box_types() -> Dict[str, Dict[str, str]]:
    """정보 박스 타입별 스타일 정보 반환"""
    return {
        'info': {
            'icon': 'ℹ️',
            'background': '#e1f5fe',
            'border': '#0288d1',
            'color': '#01579b'
        },
        'warning': {
            'icon': '⚠️',
            'background': '#fff8e1',
            'border': '#ffa000',
            'color': '#e65100'
        },
        'error': {
            'icon': '❌',
            'background': '#ffebee',
            'border': '#d32f2f',
            'color': '#b71c1c'
        },
        'success': {
            'icon': '✅',
            'background': '#e8f5e8',
            'border': '#4caf50',
            'color': '#2e7d32'
        }
    }

def get_walb_service_info() -> Dict[str, str]:
    """WALB 서비스 정보 반환"""
    return {
        'service_account_id': '292967571836',
        'service_name': 'WALB (Web AWS Landing Baseline)',
        'external_id_prefix': 'walb-',
        'trust_policy_statement_id': 'WALBTrustRelationship'
    }

class ConnectionConfig:
    """Connection 설정 클래스 - 모든 설정과 상수 중앙화"""
    
    def __init__(self):
        """설정 초기화"""
        self._step_definitions = get_step_definitions()
        self._connection_types = get_connection_types()
        self._available_regions = get_available_regions()
        self._test_services = get_test_services()
        self._validation_rules = get_validation_rules()
        self._default_session_state = get_default_session_state()
        self._info_box_types = get_info_box_types()
        self._walb_service_info = get_walb_service_info()
    
    def get_step_by_number(self, step_number: int) -> Dict[str, Any]:
        """단계 번호로 단계 정보 반환"""
        for step in self._step_definitions:
            if step['number'] == step_number:
                return step
        return {}
    
    def get_connection_type_info(self, connection_type: str) -> Dict[str, str]:
        """연결 타입별 정보 반환"""
        return self._connection_types.get(connection_type, {})
    
    def get_region_display_name(self, region_code: str) -> str:
        """리전 코드로 표시명 반환"""
        return self._available_regions.get(region_code, region_code)
    
    def get_validation_rule(self, field_name: str) -> Dict[str, Any]:
        """필드별 검증 규칙 반환"""
        return self._validation_rules.get(field_name, {})
    
    def get_info_box_style(self, box_type: str) -> Dict[str, str]:
        """정보 박스 타입별 스타일 반환"""
        return self._info_box_types.get(box_type, self._info_box_types['info'])
    
    def get_total_steps(self) -> int:
        """총 단계 수 반환"""
        return len(self._step_definitions)
    
    def is_valid_step(self, step_number: int) -> bool:
        """유효한 단계 번호 확인"""
        return 1 <= step_number <= self.get_total_steps()
    
    def get_service_count(self) -> int:
        """테스트할 서비스 수 반환"""
        return len(self._test_services)
    
    @property
    def step_definitions(self) -> List[Dict[str, Any]]:
        """단계 정의 반환"""
        return self._step_definitions
    
    @property
    def connection_types(self) -> Dict[str, Dict[str, str]]:
        """연결 타입 정보 반환"""
        return self._connection_types
    
    @property
    def available_regions(self) -> Dict[str, str]:
        """가용 리전 반환"""
        return self._available_regions
    
    @property
    def test_services(self) -> List[str]:
        """테스트 서비스 목록 반환"""
        return self._test_services
    
    @property
    def validation_rules(self) -> Dict[str, Any]:
        """검증 규칙 반환"""
        return self._validation_rules
    
    @property
    def default_session_state(self) -> Dict[str, Any]:
        """기본 세션 상태 반환"""
        return self._default_session_state.copy()
    
    @property
    def walb_service_info(self) -> Dict[str, str]:
        """WALB 서비스 정보 반환"""
        return self._walb_service_info