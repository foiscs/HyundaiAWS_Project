"""
WALB 진단 엔진 모듈
AWS 보안 진단의 핵심 비즈니스 로직을 담당하는 모듈

Classes:
- DiagnosisCoreEngine: AWS 보안 진단 실행 및 조치를 담당하는 핵심 엔진 클래스

Methods:
- _get_aws_handler(): AWS 연결 핸들러 싱글톤 패턴으로 관리
- _create_session(): 계정 정보를 바탕으로 AWS 세션 생성
- run_diagnosis(): 지정된 진단 항목 실행
- execute_fix(): 조치 실행 통합 로직
- validate_diagnosis_environment(): 진단 환경 검증
- get_diagnosis_checker(): 진단 체커 반환
- test_session_connection(): AWS 세션 연결 테스트 (UI 전용)
"""

import streamlit as st
from .sk_diagnosis import get_checker
from .aws_handler import AWSConnectionHandler
from botocore.exceptions import ClientError
from typing import Dict, Any, List

class DiagnosisCoreEngine:
    """AWS 보안 진단 핵심 엔진 클래스 - UI와 완전 분리된 순수 비즈니스 로직"""
    
    def __init__(self):
        self.aws_handler = self._get_aws_handler()
    
    def _get_aws_handler(self):
        """AWS 연결 핸들러를 싱글톤 패턴으로 가져옴 - 세션 상태에서 재사용"""
        if 'aws_handler' not in st.session_state:
            st.session_state.aws_handler = AWSConnectionHandler()
        return st.session_state.aws_handler
    
    def _create_session(self):
        """선택된 계정 정보로 AWS 세션 생성 - Role ARN 또는 Access Key 방식 지원"""
        account = st.session_state.selected_account
        
        if account.get('role_arn'):
            return self.aws_handler.create_session_from_role(
                role_arn=account['role_arn'],
                external_id=account.get('external_id'),
                region=account['primary_region']
            )
        else:
            return self.aws_handler.create_session_from_keys(
                access_key_id=account['access_key_id'],
                secret_access_key=account['secret_access_key'],
                region=account['primary_region']
            )
    
    def run_diagnosis(self, item_code: str, item_name: str) -> Dict[str, Any]:
        """지정된 진단 항목 실행 - 체커를 찾아 AWS 세션으로 진단 수행"""
        checker = get_checker(item_code)
        if not checker:
            return {
                "status": "not_implemented",
                "message": f"{item_name} 진단 기능이 아직 구현되지 않았습니다."
            }
        
        try:
            session = self._create_session()
            checker.session = session
            return checker.run_diagnosis()
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def execute_fix(self, selected_items: Any, item_key: str, item_code: str) -> List[Dict[str, Any]]:
        """조치 실행 통합 로직 - 체커의 execute_fix 메서드 호출"""
        checker = get_checker(item_code)
        if not checker:
            return [{
                "user": "전체",
                "action": "조치 실행",
                "status": "error",
                "error": "조치 기능을 찾을 수 없습니다."
            }]
        
        try:
            session = self._create_session()
            checker.session = session
            results = checker.execute_fix(selected_items)
            return results
                
        except Exception as e:
            return [{
                "user": "전체", 
                "action": "조치 실행",
                "status": "error",
                "error": str(e)
            }]
    
    def _execute_group_assignment(self, user_group_assignments):
        """사용자 그룹 할당 실행 - IAM 그룹에 사용자 직접 추가"""
        try:
            session = self._create_session()
            iam = session.client('iam')
            results = []
            
            for user_name, group_name in user_group_assignments.items():
                try:
                    iam.add_user_to_group(UserName=user_name, GroupName=group_name)
                    results.append({
                        "user": user_name,
                        "action": f"그룹 '{group_name}'에 추가",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "user": user_name,
                        "action": f"그룹 '{group_name}'에 추가",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "전체",
                "action": "그룹 할당",
                "status": "error",
                "error": str(e)
            }]
    
    def validate_diagnosis_environment(self) -> tuple[bool, str]:
        """진단 환경 검증 - 계정 선택 여부 및 AWS 연결 상태 확인"""
        if 'selected_account' not in st.session_state:
            return False, "선택된 계정이 없습니다."
        
        try:
            session = self._create_session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            return True, f"연결 성공: {identity['Account']}"
        except Exception as e:
            return False, f"연결 실패: {str(e)}"
    
    def get_diagnosis_checker(self, item_code):
        """진단 체커 반환 - 항목 코드로 해당 체커 모듈 가져오기"""
        return get_checker(item_code)
    
    def test_session_connection(self, account):
        """AWS 세션 연결 테스트 - UI에서 호출하여 연결 상태 확인 및 표시"""
        try:
            if account.get('role_arn'):
                # Cross-Account Role 테스트
                session = self.aws_handler.create_session_from_role(
                    role_arn=account['role_arn'],
                    external_id=account.get('external_id'),
                    region=account['primary_region']
                )
                test_message = "Role 세션 생성 성공"
            else:
                # Access Key 방식
                session = self.aws_handler.create_session_from_keys(
                    access_key_id=account['access_key_id'],
                    secret_access_key=account['secret_access_key'],
                    region=account['primary_region']
                )
                test_message = "Key 세션 생성 성공"
            
            # 간단한 STS 호출로 세션 유효성 확인
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            st.success(f"✅ {test_message}")
            st.write(f"**연결된 계정:** `{identity['Account']}`")
            st.write(f"**사용자 ARN:** `{identity['Arn']}`")
            
        except Exception as e:
            st.error(f"❌ 세션 연결 실패: {str(e)}")