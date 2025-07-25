"""
WALB Connection 비즈니스 로직 엔진
AWS 계정 연결, 테스트, 검증의 핵심 비즈니스 로직을 담당

Classes:
- ConnectionEngine: Connection 전용 비즈니스 로직 클래스

Methods:
- test_connection: AWS 연결 테스트 실행
- register_account: 계정 등록 처리
- validate_connection_form: 연결 폼 검증
- extract_account_id_from_role_arn: Role ARN에서 계정 ID 추출
- generate_external_id: External ID 생성 (aws_handler 위임)
- generate_trust_policy: Trust Policy 생성 (aws_handler 위임)
- generate_permission_policy: Permission Policy 생성 (aws_handler 위임)
- validate_input_field: 입력 필드 검증 (aws_handler 위임)
- simulate_test: 개발환경 시뮬레이션 테스트 (aws_handler 위임)
"""

import streamlit as st
import json
import time
from typing import Dict, Any, List, Tuple, Optional
from components.aws_handler import AWSConnectionHandler, InputValidator, simulate_connection_test
from components.connection_config import ConnectionConfig

class ConnectionEngine:
    """Connection 전용 비즈니스 로직 엔진 - aws_handler를 활용한 Connection 특화 로직"""
    
    def __init__(self):
        """엔진 초기화"""
        self.aws_handler = AWSConnectionHandler()
        self.config = ConnectionConfig()
        self.validator = InputValidator()
    
    def test_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """AWS 연결 테스트 실행 - connection_type에 따라 적절한 테스트 수행"""
        try:
            connection_type = connection_data.get('connection_type', 'cross-account-role')
            
            if connection_type == 'cross-account-role':
                return self._test_cross_account_connection(connection_data)
            elif connection_type == 'access-key':
                return self._test_access_key_connection(connection_data)
            else:
                return {
                    'status': 'error',
                    'message': f'지원하지 않는 연결 방식입니다: {connection_type}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'연결 테스트 중 오류 발생: {str(e)}'
            }
    
    def _test_cross_account_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-Account Role 연결 테스트"""
        role_arn = connection_data.get('role_arn', '')
        external_id = connection_data.get('external_id', '')
        region = connection_data.get('primary_region', 'ap-northeast-2')
        
        # 개발환경 시뮬레이션 체크
        if st.secrets.get("DEVELOPMENT_MODE", False):
            return simulate_connection_test(connection_data)
        
        return self.aws_handler.test_cross_account_connection(role_arn, external_id, region)
    
    def _test_access_key_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Access Key 연결 테스트"""
        access_key_id = connection_data.get('access_key_id', '')
        secret_access_key = connection_data.get('secret_access_key', '')
        region = connection_data.get('primary_region', 'ap-northeast-2')
        
        # 개발환경 시뮬레이션 체크
        if st.secrets.get("DEVELOPMENT_MODE", False):
            return simulate_connection_test(connection_data)
        
        return self.aws_handler.test_access_key_connection(access_key_id, secret_access_key, region)
    
    def register_account(self, account_data: Dict[str, Any]) -> Tuple[bool, str]:
        """계정 등록 처리 - registered_accounts.json에 저장"""
        try:
            # 계정 데이터 복사 및 정리
            account = account_data.copy()
            
            # Role ARN에서 계정 ID 추출 (Cross-Account Role 방식인 경우)
            if account.get('connection_type') == 'cross-account-role' and account.get('role_arn'):
                extracted_account_id = self.extract_account_id_from_role_arn(account['role_arn'])
                if extracted_account_id:
                    account['account_id'] = extracted_account_id
            
            # 계정 정보 유효성 검증
            validation_result = self.validate_account_data(account)
            if not validation_result[0]:
                return False, f"계정 정보 검증 실패: {validation_result[1]}"
            
            # 파일에 저장
            with open("registered_accounts.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(account, ensure_ascii=False) + "\n")
            
            return True, "AWS 계정이 성공적으로 등록되었습니다"
            
        except Exception as e:
            return False, f"계정 등록 중 오류 발생: {str(e)}"
    
    def validate_connection_form(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """연결 폼 전체 검증 - 모든 필수 필드와 형식 검증"""
        errors = []
        connection_type = form_data.get('connection_type', 'cross-account-role')
        
        # 공통 필드 검증
        if form_data.get('contact_email', '').strip() and not self.validator.validate_email(form_data['contact_email']):
            errors.append("올바른 이메일 형식을 입력해주세요")
        
        # 연결 방식별 검증
        if connection_type == 'cross-account-role':
            errors.extend(self._validate_cross_account_fields(form_data))
        elif connection_type == 'access-key':
            errors.extend(self._validate_access_key_fields(form_data))
        
        return len(errors) == 0, errors
    
    def _validate_cross_account_fields(self, form_data: Dict[str, Any]) -> List[str]:
        """Cross-Account Role 필드 검증"""
        errors = []
        
        role_arn = form_data.get('role_arn', '').strip()
        external_id = form_data.get('external_id', '').strip()
        
        if role_arn and not self.validator.validate_role_arn(role_arn):
            errors.append("올바른 IAM Role ARN 형식을 입력해주세요")
        
        if not external_id:
            errors.append("External ID를 입력해주세요")
        elif len(external_id) < 6:
            errors.append("External ID는 6자 이상이어야 합니다")
        
        return errors
    
    def _validate_access_key_fields(self, form_data: Dict[str, Any]) -> List[str]:
        """Access Key 필드 검증"""
        errors = []
        
        access_key_id = form_data.get('access_key_id', '').strip()
        secret_access_key = form_data.get('secret_access_key', '').strip()
        
        if not access_key_id:
            errors.append("Access Key ID를 입력해주세요")
        elif not self.validator.validate_access_key(access_key_id):
            errors.append("올바른 Access Key ID 형식을 입력해주세요")
        
        if not secret_access_key:
            errors.append("Secret Access Key를 입력해주세요")
        elif not self.validator.validate_secret_key(secret_access_key):
            errors.append("올바른 Secret Access Key 형식을 입력해주세요")
        
        return errors
    
    def validate_account_data(self, account_data: Dict[str, Any]) -> Tuple[bool, str]:
        """최종 계정 데이터 검증"""
        try:
            # 필수 필드 확인
            required_fields = ['cloud_name', 'contact_email', 'primary_region']
            
            for field in required_fields:
                if not account_data.get(field, '').strip():
                    return False, f"필수 필드가 누락되었습니다: {field}"
            
            # 연결 방식별 필수 필드 확인
            connection_type = account_data.get('connection_type', 'cross-account-role')
            
            if connection_type == 'cross-account-role':
                if not account_data.get('role_arn', '').strip():
                    return False, "Role ARN이 누락되었습니다"
                if not account_data.get('external_id', '').strip():
                    return False, "External ID가 누락되었습니다"
            
            elif connection_type == 'access-key':
                if not account_data.get('access_key_id', '').strip():
                    return False, "Access Key ID가 누락되었습니다"
                if not account_data.get('secret_access_key', '').strip():
                    return False, "Secret Access Key가 누락되었습니다"
            
            return True, "검증 완료"
            
        except Exception as e:
            return False, f"검증 중 오류 발생: {str(e)}"
    
    def extract_account_id_from_role_arn(self, role_arn: str) -> Optional[str]:
        """Role ARN에서 12자리 계정 ID 추출"""
        try:
            # ARN 형식: arn:aws:iam::123456789012:role/role-name
            parts = role_arn.split(':')
            if len(parts) >= 5 and parts[4].isdigit() and len(parts[4]) == 12:
                return parts[4]
            return None
        except Exception:
            return None
    
    def generate_external_id(self) -> str:
        """External ID 생성 - aws_handler 위임"""
        return self.aws_handler.generate_external_id()
    
    def generate_trust_policy(self, external_id: str) -> Dict[str, Any]:
        """Trust Policy 생성 - aws_handler 위임"""
        return self.aws_handler.generate_trust_policy(external_id)
    
    def generate_permission_policy(self) -> Dict[str, Any]:
        """Permission Policy 생성 - aws_handler 위임"""
        return self.aws_handler.generate_permission_policy()
    
    def validate_input_field(self, field_type: str, value: str) -> Tuple[bool, str]:
        """입력 필드 검증 - aws_handler InputValidator 위임"""
        try:
            if field_type == 'account_id':
                is_valid = self.validator.validate_account_id(value)
                message = "올바른 12자리 계정 ID입니다" if is_valid else "12자리 숫자로 입력해주세요"
            elif field_type == 'role_arn':
                is_valid = self.validator.validate_role_arn(value)
                message = "올바른 Role ARN 형식입니다" if is_valid else "올바른 Role ARN 형식을 입력해주세요"
            elif field_type == 'access_key':
                is_valid = self.validator.validate_access_key(value)
                message = "올바른 Access Key 형식입니다" if is_valid else "올바른 Access Key 형식을 입력해주세요"
            elif field_type == 'secret_key':
                is_valid = self.validator.validate_secret_key(value)
                message = "올바른 Secret Key 형식입니다" if is_valid else "올바른 Secret Key 형식을 입력해주세요"
            elif field_type == 'email':
                is_valid = self.validator.validate_email(value)
                message = "올바른 이메일 형식입니다" if is_valid else "올바른 이메일 형식을 입력해주세요"
            else:
                is_valid = True
                message = ""
            
            return is_valid, message
            
        except Exception as e:
            return False, f"검증 중 오류: {str(e)}"
    
    def simulate_test(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """개발환경 시뮬레이션 테스트 - aws_handler 위임"""
        return simulate_connection_test(connection_data)
    
    def get_connection_type_info(self, connection_type: str) -> Dict[str, str]:
        """연결 타입 정보 반환 - config 위임"""
        return self.config.get_connection_type_info(connection_type)
    
    def get_available_regions(self) -> Dict[str, str]:
        """사용 가능한 리전 목록 반환 - config 위임"""
        return self.config.available_regions
    
    def safe_step_change(self, new_step: int) -> bool:
        """안전한 단계 변경 - 세션 상태 업데이트"""
        try:
            if self.config.is_valid_step(new_step) and st.session_state.current_step != new_step:
                st.session_state.current_step = new_step
                return True
            return False
        except Exception:
            return False
    
    def cleanup_sensitive_data(self) -> None:
        """보안을 위한 민감정보 자동 정리"""
        try:
            # 세션에서 민감 정보 제거
            sensitive_keys = ['secret_access_key', 'test_results']
            for key in sensitive_keys:
                if key in st.session_state:
                    del st.session_state[key]
        except Exception:
            pass
    
    def get_walb_service_account_id(self) -> str:
        """WALB 서비스 계정 ID 반환"""
        return self.config.walb_service_info['service_account_id']