"""
1.2 IAM 사용자 계정 단일화 관리 진단
"""
import boto3
from datetime import datetime, timezone
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class IAMSingleAccountChecker(BaseChecker):
    """1.2 IAM 사용자 계정 단일화 관리 진단"""
    
    @property
    def item_code(self):
        return "1.2"
    
    @property 
    def item_name(self):
        return "IAM 사용자 계정 단일화 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 콘솔 로그인 및 Access Key 사용 이력을 기준으로
          90일 이상 미사용된 IAM 사용자를 찾아냅니다.
        - 단, 1명의 담당자가 다수의 계정을 사용하는지 여부는 수동 점검 필요
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            inactive_user_details = {}
            now = datetime.now(timezone.utc)

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    is_inactive = True

                    # 콘솔 로그인 사용 이력 확인
                    last_password_use = user.get('PasswordLastUsed')
                    if last_password_use and (now - last_password_use).days <= 90:
                        is_inactive = False

                    # Access Key 사용 이력 또는 생성일 확인
                    if is_inactive:
                        keys_response = iam.list_access_keys(UserName=user_name)
                        has_active_key = False

                        for key in keys_response['AccessKeyMetadata']:
                            if key['Status'] == 'Active':
                                has_active_key = True
                                last_used_info = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                                last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                                create_date = key['CreateDate']

                                if last_used_date:
                                    if (now - last_used_date).days <= 90:
                                        is_inactive = False
                                        break
                                else:
                                    # 사용 이력은 없지만 생성된 지 90일 미만이면 활성으로 간주
                                    if (now - create_date).days <= 90:
                                        is_inactive = False
                                        break

                        # 판단 결과에 따라 사용자 분류
                        if has_active_key and is_inactive:
                            inactive_user_details[user_name] = "액세스 키 90일 이상 미사용"
                        elif not has_active_key and not last_password_use:
                            inactive_user_details[user_name] = "활동 기록 없음"
                        elif is_inactive and last_password_use:
                            inactive_user_details[user_name] = f"콘솔 비활성: {(now - last_password_use).days}일"

            # 위험도 계산
            inactive_count = len(inactive_user_details)
            risk_level = self.calculate_risk_level(
                inactive_count,
                2 if inactive_count > 3 else 1  # 많은 비활성 계정은 더 심각
            )

            return {
                "status": "success",
                "inactive_users": dict(inactive_user_details),
                "inactive_count": inactive_count,
                "risk_level": risk_level,
                "has_issues": inactive_count > 0,
                "manual_check_required": True  # 수동 점검 필요 표시
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """1.2 진단 결과 UI 렌더링"""
        st.write(f"🔍 **비활성 사용자:** {result['inactive_count']}개")
        
        if result.get('manual_check_required'):
            st.warning("⚠️ 1명의 담당자가 여러 개의 IAM 계정을 사용하는지에 대해서는 수동 점검이 필요합니다.")
        
        if result['inactive_users']:
            with st.expander("비활성 사용자 목록 보기"):
                for user, reason in result['inactive_users'].items():
                    st.write(f"• `{user}` - {reason}")
        
        # 조치 버튼
        if result.get('has_issues', False):
            if st.button("🔧 즉시 조치", key=f"fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
            
            if st.session_state.get(f'show_fix_{item_key}', False):
                ui_handler.show_fix_form(result, item_key, self.item_code)
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """1.2 조치 폼 UI 렌더링"""
        with st.form(f"fix_form_{item_key}"):
            st.markdown("**🔧 조치할 항목을 선택하세요:**")
            st.warning("⚠️ 선택된 사용자들의 Access Key가 비활성화되고 콘솔 로그인이 차단됩니다.")
            
            selected_inactive_users = []
            
            if result['inactive_users']:
                st.markdown("**비활성 사용자 처리:**")
                for user, reason in result['inactive_users'].items():
                    if st.checkbox(f"`{user}` - {reason}", key=f"inactive_{item_key}_{user}"):
                        selected_inactive_users.append(user)
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("🚀 조치 실행", type="primary"):
                    if selected_inactive_users:
                        selected_items = {'inactive_users': selected_inactive_users}
                        ui_handler.execute_fix(selected_items, item_key, self.item_code)
                    else:
                        st.warning("조치할 항목을 선택해주세요.")
            
            with col_submit2:
                if st.form_submit_button("❌ 취소"):
                    st.session_state[f'show_fix_{item_key}'] = False
                    st.rerun()
                    
    def execute_fix(self, selected_items):
        """
        조치 실행
        - 선택된 비활성 사용자들의 Access Key 비활성화
        - 콘솔 로그인 비활성화
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            results = []
            
            # 비활성 사용자 조치
            for user in selected_items.get('inactive_users', []):
                user_results = []
                
                # 1. Access Key 비활성화
                try:
                    keys_response = iam.list_access_keys(UserName=user)
                    for key in keys_response['AccessKeyMetadata']:
                        if key['Status'] == 'Active':
                            iam.update_access_key(
                                UserName=user,
                                AccessKeyId=key['AccessKeyId'],
                                Status='Inactive'
                            )
                            user_results.append("Access Key 비활성화")
                except ClientError as e:
                    user_results.append(f"Access Key 비활성화 실패: {str(e)}")
                
                # 2. 콘솔 로그인 비활성화 (로그인 프로필 삭제)
                try:
                    iam.delete_login_profile(UserName=user)
                    user_results.append("콘솔 로그인 비활성화")
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchEntity':
                        user_results.append(f"콘솔 로그인 비활성화 실패: {str(e)}")
                    else:
                        user_results.append("콘솔 로그인 프로필 없음")
                
                # 결과 추가
                if user_results:
                    results.append({
                        "user": user,
                        "status": "success",
                        "actions": user_results
                    })
                else:
                    results.append({
                        "user": user,
                        "status": "no_action",
                        "message": "조치할 항목 없음"
                    })

            return results

        except ClientError as e:
            return [{
                "status": "error",
                "error_message": str(e)
            }]