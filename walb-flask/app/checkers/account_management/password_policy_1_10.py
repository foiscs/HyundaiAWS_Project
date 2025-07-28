"""
1.10 패스워드 정책 진단 (Flask용)
mainHub의 password_policy_1_10.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class PasswordPolicyChecker(BaseChecker):
    """1.10 패스워드 정책 진단"""
    
    @property
    def item_code(self):
        return "1.10"
    
    @property 
    def item_name(self):
        return "패스워드 정책"
    
    def run_diagnosis(self):
        """
        진단 수행 - IAM 패스워드 정책 설정 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            try:
                policy = iam.get_account_password_policy()
                password_policy = policy['PasswordPolicy']
                policy_exists = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    password_policy = {}
                    policy_exists = False
                else:
                    raise e
            
            # 권장 정책 기준
            recommendations = {
                'MinimumPasswordLength': 14,
                'RequireSymbols': True,
                'RequireNumbers': True,
                'RequireUppercaseCharacters': True,
                'RequireLowercaseCharacters': True,
                'MaxPasswordAge': 90,
                'PasswordReusePrevention': 24,
                'AllowUsersToChangePassword': True
            }
            
            policy_issues = []
            
            if not policy_exists:
                policy_issues.append("패스워드 정책이 설정되지 않았습니다.")
            else:
                for key, recommended_value in recommendations.items():
                    current_value = password_policy.get(key)
                    
                    if key == 'MinimumPasswordLength':
                        if not current_value or current_value < recommended_value:
                            policy_issues.append(f"최소 패스워드 길이가 {recommended_value}자 미만입니다. (현재: {current_value or 0})")
                    
                    elif key == 'MaxPasswordAge':
                        if not current_value or current_value > recommended_value:
                            policy_issues.append(f"패스워드 만료 기간이 {recommended_value}일을 초과합니다. (현재: {current_value or '무제한'})")
                    
                    elif key == 'PasswordReusePrevention':
                        if not current_value or current_value < recommended_value:
                            policy_issues.append(f"패스워드 재사용 방지 설정이 {recommended_value}개 미만입니다. (현재: {current_value or 0})")
                    
                    elif isinstance(recommended_value, bool) and recommended_value:
                        if not current_value:
                            policy_name = {
                                'RequireSymbols': '특수문자 필수',
                                'RequireNumbers': '숫자 필수',
                                'RequireUppercaseCharacters': '대문자 필수',
                                'RequireLowercaseCharacters': '소문자 필수',
                                'AllowUsersToChangePassword': '사용자 패스워드 변경 허용'
                            }.get(key, key)
                            policy_issues.append(f"{policy_name} 설정이 비활성화되어 있습니다.")
            
            # 위험도 계산
            issues_count = len(policy_issues)
            risk_level = self.calculate_risk_level(
                issues_count,
                3 if not policy_exists else 2  # 정책 없음은 매우 높은 위험도
            )
            
            return {
                "status": "success",
                "policy_exists": policy_exists,
                "current_policy": password_policy,
                "policy_issues": policy_issues,
                "issues_count": issues_count,
                "recommendations": recommendations,
                "risk_level": risk_level,
                "has_issues": issues_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if not result.get('policy_exists'):
            return "⚠️ IAM 패스워드 정책이 설정되지 않았습니다."
        
        issues_count = result.get('issues_count', 0)
        if issues_count > 0:
            return f"⚠️ 패스워드 정책에서 {issues_count}개의 보안 취약점이 발견되었습니다."
        else:
            return "✅ 패스워드 정책이 보안 권장사항에 따라 적절히 설정되어 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "패스워드 정책 상태": {
                "정책 존재 여부": "설정됨" if result.get('policy_exists') else "미설정",
                "발견된 문제": result.get('issues_count', 0),
                "recommendation": "강력한 패스워드 정책을 설정하여 계정 보안을 강화하세요."
            }
        }
        
        if result.get('policy_issues'):
            details["보안 취약점"] = {
                "issues": result['policy_issues'],
                "recommendation": "모든 취약점을 수정하여 보안을 강화하세요."
            }
        
        if result.get('current_policy'):
            details["현재 정책 설정"] = result['current_policy']
        
        details["권장 정책 설정"] = result.get('recommendations', {})
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        return [{
            "type": "apply_secure_password_policy",
            "title": "보안 패스워드 정책 적용",
            "description": "권장 보안 기준에 따라 패스워드 정책을 설정합니다.",
            "items": [{"setting": issue, "action": "보안 정책 적용"} 
                     for issue in result.get('policy_issues', [])],
            "severity": "high"
        }]
    
    def execute_fix(self, selected_items):
        """조치 실행 - 보안 패스워드 정책 적용"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            # 권장 패스워드 정책 적용
            secure_policy = {
                'MinimumPasswordLength': 14,
                'RequireSymbols': True,
                'RequireNumbers': True,
                'RequireUppercaseCharacters': True,
                'RequireLowercaseCharacters': True,
                'MaxPasswordAge': 90,
                'PasswordReusePrevention': 24,
                'AllowUsersToChangePassword': True,
                'HardExpiry': False
            }
            
            try:
                iam.update_account_password_policy(**secure_policy)
                return [{
                    "action": "보안 패스워드 정책 적용",
                    "status": "success",
                    "details": "권장 보안 기준에 따라 패스워드 정책이 설정되었습니다."
                }]
            except ClientError as e:
                return [{
                    "action": "보안 패스워드 정책 적용",
                    "status": "error",
                    "error": str(e)
                }]
            
        except Exception as e:
            return [{
                "action": "패스워드 정책 설정",
                "status": "error",
                "error": str(e)
            }]