"""
WALB 세션 상태 관리 중앙화 모듈
모든 페이지에서 일관된 세션 상태 초기화 및 관리
"""

import streamlit as st
from datetime import datetime
from components.aws_handler import AWSConnectionHandler

class SessionManager:
    """중앙집중식 세션 상태 관리 클래스"""
    
    # 기본 세션 상태 정의
    DEFAULT_SESSION_STATE = {
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
    
    @staticmethod
    def initialize_session(force_reset=False):
        """
        세션 상태 초기화 - 중복 방지 로직 포함
        
        Args:
            force_reset (bool): 강제 초기화 여부
        """
        # 이미 초기화되었고 강제 초기화가 아닌 경우 스킵
        if not force_reset and st.session_state.get('session_initialized', False):
            return
        
        # 기본 상태 설정
        for key, value in SessionManager.DEFAULT_SESSION_STATE.items():
            if key not in st.session_state or force_reset:
                if key == 'account_data' and isinstance(value, dict):
                    # 중첩 딕셔너리는 새로운 인스턴스로 생성
                    st.session_state[key] = value.copy()
                else:
                    st.session_state[key] = value
        
        # AWS 핸들러 초기화
        if 'aws_handler' not in st.session_state or force_reset:
            st.session_state.aws_handler = AWSConnectionHandler()
        
        # 초기화 시간 기록
        st.session_state.initialized_at = datetime.now()
        st.session_state.session_initialized = True
    
    @staticmethod
    def reset_connection_data(keep_aws_handler=True):
        """
        연결 관련 데이터만 초기화 (단계별 진행 중 사용)
        
        Args:
            keep_aws_handler (bool): AWS 핸들러 유지 여부
        """
        # 연결 관련 데이터만 초기화
        reset_keys = ['connection_status', 'test_results', 'security_warnings']
        
        for key in reset_keys:
            if key in SessionManager.DEFAULT_SESSION_STATE:
                st.session_state[key] = SessionManager.DEFAULT_SESSION_STATE[key]
        
        # account_data 일부 초기화 (민감정보 제거)
        if 'account_data' in st.session_state:
            st.session_state.account_data['secret_access_key'] = ''
            if 'external_id' in st.session_state.account_data:
                st.session_state.account_data['external_id'] = ''
        
        # 임시 Secret Key 제거
        if 'temp_secret_key' in st.session_state:
            del st.session_state['temp_secret_key']
    
    @staticmethod
    def reset_all(keep_aws_handler=False):
        """
        전체 세션 상태 완전 초기화
        
        Args:
            keep_aws_handler (bool): AWS 핸들러 유지 여부
        """
        # 보존할 핸들러 백업
        aws_handler = st.session_state.get('aws_handler') if keep_aws_handler else None
        
        # 전체 세션 클리어
        for key in list(st.session_state.keys()):
            if key.startswith(('current_step', 'connection_', 'account_data', 
                              'test_results', 'security_warnings', 'diagnosis_',
                              'show_', 'temp_')):
                del st.session_state[key]
        
        # 기본 상태로 재초기화
        SessionManager.initialize_session(force_reset=True)
        
        # AWS 핸들러 복원
        if aws_handler and keep_aws_handler:
            st.session_state.aws_handler = aws_handler
    
    @staticmethod
    def cleanup_sensitive_data():
        """민감정보 정리"""
        # 임시 Secret Key 제거
        if 'temp_secret_key' in st.session_state:
            del st.session_state['temp_secret_key']
        
        # Secret Key 마스킹
        if 'account_data' in st.session_state:
            if st.session_state.account_data.get('secret_access_key'):
                if st.session_state.account_data['secret_access_key'] != '[MASKED]':
                    st.session_state.account_data['secret_access_key'] = '[MASKED]'
    
    @staticmethod
    def get_session_summary():
        """세션 상태 요약 정보 반환 (디버깅용)"""
        return {
            'initialized': st.session_state.get('session_initialized', False),
            'initialized_at': st.session_state.get('initialized_at'),
            'current_step': st.session_state.get('current_step', 'unknown'),
            'connection_type': st.session_state.get('connection_type', 'unknown'),
            'connection_status': st.session_state.get('connection_status', 'unknown'),
            'has_account_data': bool(st.session_state.get('account_data', {})),
            'has_aws_handler': bool(st.session_state.get('aws_handler')),
            'has_selected_account': bool(st.session_state.get('selected_account')),
            'total_keys': len(st.session_state.keys()),
            'diagnosis_states': len([k for k in st.session_state.keys() if k.startswith('diagnosis_')])
        }
    
    @staticmethod
    def ensure_diagnosis_session():
        """진단 페이지용 세션 확인 및 초기화"""
        # 기본 세션 초기화
        SessionManager.initialize_session()
        
        # 선택된 계정 정보 확인
        if 'selected_account' not in st.session_state:
            return False, "선택된 계정이 없습니다."
        
        # AWS 핸들러 확인
        if 'aws_handler' not in st.session_state:
            st.session_state.aws_handler = AWSConnectionHandler()
        
        return True, "세션 준비 완료"
    
    @staticmethod
    def clear_diagnosis_states():
        """진단 관련 상태만 초기화"""
        keys_to_delete = []
        for key in st.session_state.keys():
            if key.startswith(('diagnosis_status_', 'diagnosis_result_', 'show_fix_')):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]