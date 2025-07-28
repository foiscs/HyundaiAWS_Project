"""
1.9 MFA 설정 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class MFASettingChecker(BaseChecker):
    """1.9 MFA 설정 진단"""
    
    @property
    def item_code(self):
        return "1.9"
    
    @property 
    def item_name(self):
        return "MFA 설정"
    
    def run_diagnosis(self):
        """
        진단 수행
        - Root 계정 및 콘솔 사용자에 대해 MFA 활성화 여부를 점검하고 미설정 사용자 목록을 반환
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            root_mfa_disabled = False
            users_without_mfa = []
            total_console_users = 0
            
            # Root 계정 MFA 확인
            try:
                account_summary = iam.get_account_summary()
                if account_summary['SummaryMap']['AccountMFAEnabled'] == 0:
                    root_mfa_disabled = True
            except ClientError as e:
                return {
                    "status": "error",
                    "error_message": f"계정 요약 정보를 가져오는 중 오류 발생: {str(e)}"
                }
            
            # IAM 사용자 MFA 확인
            try:
                paginator = iam.get_paginator('list_users')
                for page in paginator.paginate():
                    for user in page['Users']:
                        user_name = user['UserName']
                        
                        # 콘솔 로그인 가능한 사용자인지 확인
                        try:
                            iam.get_login_profile(UserName=user_name)
                            total_console_users += 1
                            
                            # MFA 디바이스 확인
                            mfa_devices = iam.list_mfa_devices(UserName=user_name)
                            if not mfa_devices.get('MFADevices'):
                                users_without_mfa.append(user_name)
                                
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'NoSuchEntity':
                                # 콘솔 로그인 프로파일이 없음 (콘솔 접근 불가 사용자)
                                continue
                            else:
                                raise e
                                
            except ClientError as e:
                return {
                    "status": "error", 
                    "error_message": f"IAM 사용자 MFA 정보를 가져오는 중 오류 발생: {str(e)}"
                }
            
            # 위험도 계산
            issues_count = (1 if root_mfa_disabled else 0) + len(users_without_mfa)
            risk_level = self.calculate_risk_level(issues_count, 2)  # MFA는 중요하므로 가중치 2
            
            return {
                "status": "success",
                "root_mfa_disabled": root_mfa_disabled,
                "users_without_mfa": users_without_mfa,
                "total_console_users": total_console_users,
                "users_without_mfa_count": len(users_without_mfa),
                "risk_level": risk_level,
                "has_issues": root_mfa_disabled or len(users_without_mfa) > 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.9 진단 결과 UI 렌더링"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Root 계정 MFA 상태
            if result.get('root_mfa_disabled', False):
                st.error("🔴 Root 계정 MFA 비활성화")
                st.caption("Root 계정에 MFA가 설정되지 않았습니다")
            else:
                st.success("✅ Root 계정 MFA 활성화")
                st.caption("Root 계정에 MFA가 적절히 설정되어 있습니다")
        
        with col2:
            # IAM 사용자 MFA 상태
            users_without_mfa_count = result.get('users_without_mfa_count', 0)
            total_console_users = result.get('total_console_users', 0)
            
            if users_without_mfa_count > 0:
                st.error(f"🔴 MFA 미설정 사용자: {users_without_mfa_count}명")
                st.caption(f"총 {total_console_users}명의 콘솔 사용자 중 {users_without_mfa_count}명이 MFA 미설정")
            else:
                st.success("✅ 모든 사용자 MFA 설정 완료")
                st.caption(f"총 {total_console_users}명의 콘솔 사용자 모두 MFA 설정됨")
        
        # 상세 정보 표시
        if result.get('has_issues', False):
            with st.expander("🔍 상세 정보", expanded=False):
                if result.get('root_mfa_disabled', False):
                    st.warning("**Root 계정 MFA 미설정**")
                    st.write("- Root 계정에 MFA가 활성화되어 있지 않습니다")
                    st.write("- AWS Management Console에 Root로 로그인하여 [내 보안 자격 증명]에서 MFA 디바이스를 설정하세요")
                
                users_without_mfa = result.get('users_without_mfa', [])
                if users_without_mfa:
                    st.warning("**MFA 미설정 사용자 목록**")
                    for i, user in enumerate(users_without_mfa, 1):
                        st.write(f"{i}. `{user}`")
                    st.write("- 각 사용자는 AWS Management Console에 로그인하여 [내 보안 자격 증명]에서 MFA를 설정해야 합니다")
    
    def render_fix_form(self, result, item_key, ui_handler):
        """1.9 조치 폼 렌더링"""
        st.error("⚠️ **반드시 수동 조치 필요**")
        st.write("MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없습니다.")
        
        if result.get('root_mfa_disabled', False):
            st.warning("**Root 계정 MFA 설정 방법:**")
            st.write("""
            1. AWS Management Console에 Root 계정으로 로그인
            2. 우측 상단 계정명 클릭 → [내 보안 자격 증명]
            3. [멀티 팩터 인증(MFA)] 섹션에서 [MFA 활성화] 클릭
            4. 가상 MFA 디바이스 선택 후 QR 코드를 Google Authenticator 등의 앱으로 스캔
            5. 연속된 두 개의 MFA 코드 입력하여 설정 완료
            """)
        
        users_without_mfa = result.get('users_without_mfa', [])
        if users_without_mfa:
            st.warning("**IAM 사용자 MFA 설정 방법:**")
            st.write("다음 사용자들에게 MFA 설정을 안내하세요:")
            for user in users_without_mfa:
                st.write(f"• `{user}`")
            
            st.write("""
            **각 사용자별 설정 방법:**
            1. AWS Management Console에 해당 IAM 사용자로 로그인
            2. 우측 상단 계정명 클릭 → [내 보안 자격 증명]
            3. [멀티 팩터 인증(MFA)] 섹션에서 [MFA 디바이스 할당] 클릭
            4. 가상 MFA 디바이스 선택 후 QR 코드를 Google Authenticator 등의 앱으로 스캔
            5. 연속된 두 개의 MFA 코드 입력하여 설정 완료
            """)
        
        # 확인 버튼 (실제 조치는 불가하지만 안내 완료 확인용)
        if st.button("📋 안내 확인 완료", key=f"mfa_guide_confirm_{item_key}"):
            st.success("✅ **수동 조치 안내 완료** - 각 사용자가 개별적으로 MFA를 설정하도록 안내하세요.")
            st.session_state[f'fix_completed_{item_key}'] = True
            st.rerun()
    
    def execute_fix(self, selected_items):
        """
        조치 실행
        MFA 설정은 사용자의 물리적 디바이스가 필요하므로 자동 조치가 불가능함
        """
        return [{
            "status": "no_action",
            "user": "시스템",
            "message": "MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없습니다. 수동 설정 안내를 참조하세요."
        }]