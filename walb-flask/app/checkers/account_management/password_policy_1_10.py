"""
1.10 패스워드 정책 체커
AWS 계정의 패스워드 정책을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class PasswordPolicyChecker(BaseChecker):
    """1.10 패스워드 정책 체커"""
    
    @property
    def item_code(self):
        return "1.10"
    
    @property 
    def item_name(self):
        return "패스워드 정책"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            policy_issues = []
            current_policy = {}
            policy_exists = False
            
            try:
                # 계정 패스워드 정책 확인
                response = iam.get_account_password_policy()
                current_policy = response.get('PasswordPolicy', {})
                policy_exists = True
                
                # 각 정책 항목 검사
                min_length = current_policy.get('MinimumPasswordLength', 0)
                if min_length < 8:
                    policy_issues.append({
                        'issue': 'minimum_length',
                        'current': min_length,
                        'required': 8,
                        'description': f'최소 길이가 {min_length}자로 권장 기준(8자) 미만입니다.'
                    })
                
                # 복잡도 요구사항 검사
                complexity_requirements = [
                    ('RequireSymbols', '특수문자'),
                    ('RequireNumbers', '숫자'),
                    ('RequireUppercaseCharacters', '대문자'),
                    ('RequireLowercaseCharacters', '소문자')
                ]
                
                missing_complexity = []
                for req_key, req_name in complexity_requirements:
                    if not current_policy.get(req_key, False):
                        missing_complexity.append(req_name)
                
                if len(missing_complexity) > 1:  # 3개 이상 요구, 즉 2개 이상 빠지면 문제
                    policy_issues.append({
                        'issue': 'complexity',
                        'missing': missing_complexity,
                        'description': f'복잡도 요구사항 부족: {", ".join(missing_complexity)} 미설정'
                    })
                
                # 재사용 방지 검사
                reuse_prevention = current_policy.get('PasswordReusePrevention', 0)
                if reuse_prevention < 5:
                    policy_issues.append({
                        'issue': 'reuse_prevention',
                        'current': reuse_prevention,
                        'required': 5,
                        'description': f'패스워드 재사용 방지가 {reuse_prevention}회로 권장 기준(5회) 미만입니다.'
                    })
                
                # 만료 기간 검사
                expire_passwords = current_policy.get('ExpirePasswords', False)
                max_age = current_policy.get('MaxPasswordAge', 0)
                if not expire_passwords or max_age > 90:
                    policy_issues.append({
                        'issue': 'password_expiry',
                        'current': max_age if expire_passwords else '미설정',
                        'required': 90,
                        'description': f'패스워드 만료가 {"미설정" if not expire_passwords else f"{max_age}일"}으로 권장 기준(90일) 초과 또는 미설정입니다.'
                    })
                
                # 사용자 변경 권한 검사
                if not current_policy.get('AllowUsersToChangePassword', False):
                    policy_issues.append({
                        'issue': 'user_change_permission',
                        'description': '사용자 패스워드 변경 권한이 비활성화되어 있습니다.'
                    })
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    # 패스워드 정책이 아예 없는 경우
                    policy_exists = False
                    policy_issues.append({
                        'issue': 'no_policy',
                        'description': '계정에 패스워드 정책이 설정되어 있지 않습니다.'
                    })
                else:
                    return {
                        'status': 'error',
                        'error_message': f'패스워드 정책을 조회하는 중 오류가 발생했습니다: {str(e)}'
                    }
            
            # 결과 분석
            has_issues = len(policy_issues) > 0
            risk_level = self.calculate_risk_level(len(policy_issues), severity_score=1.5)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'policy_exists': policy_exists,
                'current_policy': current_policy,
                'policy_issues': policy_issues,
                'issues_count': len(policy_issues),
                'recommendation': "[ⓘ INFO] Admin Console의 패스워드 복잡성 정책은 AWS 내부 정책에 의해 관리되며, IAM 정책만 점검할 수 있습니다."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'패스워드 정책을 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            if not result.get('policy_exists'):
                return "[⚠ WARNING] 1.10 계정에 패스워드 정책이 설정되어 있지 않습니다."
            else:
                policy_issues = result.get('policy_issues', [])
                findings = [issue.get('description', '') for issue in policy_issues]
                return f"[⚠ WARNING] 1.10 패스워드 정책이 권장 기준을 충족하지 않습니다.\n  └─ 미흡 항목: {', '.join([issue.get('issue', '') for issue in policy_issues])}"
        else:
            return "[✓ COMPLIANT] 1.10 패스워드 정책이 권장 기준을 충족합니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'policy_exists': {
                'value': result.get('policy_exists', False),
                'description': '패스워드 정책 설정 여부'
            }
        }
        
        current_policy = result.get('current_policy', {})
        if current_policy:
            details['current_settings'] = {
                'minimum_length': current_policy.get('MinimumPasswordLength', 0),
                'require_symbols': current_policy.get('RequireSymbols', False),
                'require_numbers': current_policy.get('RequireNumbers', False),
                'require_uppercase': current_policy.get('RequireUppercaseCharacters', False),
                'require_lowercase': current_policy.get('RequireLowercaseCharacters', False),
                'password_reuse_prevention': current_policy.get('PasswordReusePrevention', 0),
                'expire_passwords': current_policy.get('ExpirePasswords', False),
                'max_password_age': current_policy.get('MaxPasswordAge', 0),
                'allow_users_to_change': current_policy.get('AllowUsersToChangePassword', False),
                'description': '현재 패스워드 정책 설정'
            }
        
        if result.get('has_issues'):
            policy_issues = result.get('policy_issues', [])
            details['policy_issues'] = {
                'count': len(policy_issues),
                'issues': [issue.get('description', '') for issue in policy_issues],
                'description': '발견된 패스워드 정책 이슈',
                'details': policy_issues,
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        policy_issues = result.get('policy_issues', [])
        if not policy_issues:
            return None
        
        return [{
            'id': 'update_password_policy',
            'title': '권장 패스워드 정책 적용',
            'description': '권장 기준에 따라 계정 패스워드 정책을 업데이트합니다.',
            'items': [{'id': issue.get('issue', ''), 'name': issue.get('issue', ''), 'description': issue.get('description', '')} for issue in policy_issues],
            'action_type': 'update_policy'
        }]
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            results = []
            
            for fix_id, items in selected_items.items():
                if fix_id == 'update_password_policy':
                    try:
                        # 권장 기준 패스워드 정책 적용
                        iam.update_account_password_policy(
                            MinimumPasswordLength=8,
                            RequireSymbols=True,
                            RequireNumbers=True,
                            RequireUppercaseCharacters=True,
                            RequireLowercaseCharacters=True,
                            AllowUsersToChangePassword=True,
                            MaxPasswordAge=90,
                            PasswordReusePrevention=5,
                            HardExpiry=False
                        )
                        
                        results.append({
                            'item': '패스워드 정책',
                            'status': 'success',
                            'message': '권장 기준에 따라 계정 패스워드 정책이 성공적으로 업데이트되었습니다.'
                        })
                        
                        # 적용된 설정 상세 정보
                        results.append({
                            'item': '적용된 설정',
                            'status': 'info',
                            'message': '''적용된 패스워드 정책:
- 최소 길이: 8자
- 복잡도: 대문자, 소문자, 숫자, 특수문자 모두 필요
- 재사용 방지: 최근 5개 패스워드 재사용 금지
- 만료 기간: 90일
- 사용자 변경 권한: 허용'''
                        })
                        
                    except ClientError as e:
                        results.append({
                            'item': '패스워드 정책',
                            'status': 'error',
                            'message': f'패스워드 정책 업데이트 실패: {str(e)}'
                        })
            
            return results
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'패스워드 정책 업데이트 중 오류가 발생했습니다: {str(e)}'
            }]