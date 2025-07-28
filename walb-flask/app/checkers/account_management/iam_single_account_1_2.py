"""
1.2 IAM 사용자 계정 단일화 관리 진단 (Flask용)
mainHub의 iam_single_account_1_2.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from datetime import datetime, timezone
from ..base_checker import BaseChecker
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
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        inactive_count = result.get('inactive_count', 0)
        manual_check = result.get('manual_check_required', False)
        
        if inactive_count > 0:
            summary = f"⚠️ {inactive_count}개의 비활성 IAM 사용자가 발견되었습니다."
            if manual_check:
                summary += " (수동 점검 필요)"
            return summary
        else:
            return "✅ 모든 IAM 사용자가 활성 상태입니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "비활성 사용자": {
                "count": result.get('inactive_count', 0),
                "users": list(result.get('inactive_users', {}).keys()),
                "recommendation": "90일 이상 미사용 계정은 비활성화하거나 삭제하는 것을 권장합니다."
            }
        }
        
        if result.get('manual_check_required'):
            details["수동 점검 필요"] = {
                "description": "1명의 담당자가 여러 개의 IAM 계정을 사용하는지 확인 필요",
                "recommendation": "조직 내부 정책에 따라 계정 통합을 검토하세요."
            }
        
        # 비활성 사용자 상세 정보
        if result.get('inactive_users'):
            details["비활성 사용자 상세"] = {}
            for user, reason in result['inactive_users'].items():
                details["비활성 사용자 상세"][user] = reason
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        fix_options = []
        inactive_users = result.get('inactive_users', {})
        
        if inactive_users:
            fix_options.append({
                "type": "disable_inactive_users",
                "title": "비활성 사용자 비활성화",
                "description": f"{len(inactive_users)}개 비활성 사용자의 Access Key와 콘솔 로그인을 비활성화합니다.",
                "items": [{"user": user, "reason": reason, "action": "Access Key 및 콘솔 로그인 비활성화"} 
                         for user, reason in inactive_users.items()],
                "severity": "medium"
            })
        
        return fix_options
    
    def execute_fix(self, selected_items):
        """조치 실행"""
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