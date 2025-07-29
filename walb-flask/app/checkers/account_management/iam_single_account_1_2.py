"""
1.2 IAM 단일 계정 관리 체커
IAM 사용자의 단일 계정 관리 상태를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from ..base_checker import BaseChecker

class IAMSingleAccountChecker(BaseChecker):
    """1.2 IAM 단일 계정 관리 체커"""
    
    @property
    def item_code(self):
        return "1.2"
    
    @property 
    def item_name(self):
        return "IAM 단일 계정 관리"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            inactive_users = []
            all_users = []
            now = datetime.now(timezone.utc)
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    all_users.append(user_name)
                    is_inactive = True
                    
                    # 콘솔 로그인 사용 이력 확인
                    last_password_use = user.get('PasswordLastUsed')
                    if last_password_use and (now - last_password_use).days <= 90:
                        is_inactive = False
                    
                    # Access Key 사용 이력 확인
                    if is_inactive:
                        try:
                            keys_response = iam.list_access_keys(UserName=user_name)
                            for key in keys_response['AccessKeyMetadata']:
                                if key['Status'] == 'Active':
                                    try:
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
                                    except Exception:
                                        # 개별 키 조회 실패 시 건너뛰기
                                        continue
                        except Exception:
                            # 액세스 키 조회 실패 시 건너뛰기
                            continue
                    
                    # 원본 로직: 판단 결과에 따라 사용자 분류
                    if is_inactive:
                        has_active_key = False
                        try:
                            keys_response = iam.list_access_keys(UserName=user_name)
                            has_active_key = any(key['Status'] == 'Active' for key in keys_response['AccessKeyMetadata'])
                        except Exception:
                            pass
                        
                        if has_active_key and is_inactive:
                            reason = "액세스 키 90일 이상 미사용"
                        elif not has_active_key and not last_password_use:
                            reason = "활동 기록 없음"
                        elif is_inactive and last_password_use:
                            reason = f"콘솔 비활성: {(now - last_password_use).days}일"
                        else:
                            reason = "90일 이상 미활동"
                        
                        inactive_users.append({
                            'username': user_name,
                            'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                            'last_password_use': last_password_use.strftime('%Y-%m-%d') if last_password_use else 'Never',
                            'reason': reason
                        })
            
            # 결과 분석
            has_issues = len(inactive_users) > 0
            risk_level = self.calculate_risk_level(len(inactive_users))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_users': len(all_users),
                'inactive_users': inactive_users,
                'inactive_count': len(inactive_users),
                'recommendation': "[ⓘ MANUAL] 1명의 담당자가 여러 개의 IAM 계정을 사용하는지에 대해서는 수동 점검이 필요합니다."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'IAM 정보를 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            inactive_count = result.get('inactive_count', 0)
            inactive_users = result.get('inactive_users', [])
            summary = f"[참고] 1.2 미사용 사용자 계정이 존재합니다 ({inactive_count}개)."
            for user in inactive_users:
                summary += f"\n  ├─ 비활성 의심 사용자: {user['username']} ({user.get('reason', '')})"
            return summary
        else:
            return "[참고] 1.2 장기 미사용 또는 불필요한 사용자 계정이 발견되지 않았습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_users': {
                'count': result.get('total_users', 0),
                'description': '전체 IAM 사용자 수'
            }
        }
        
        if result.get('has_issues'):
            inactive_users = result.get('inactive_users', [])
            details['inactive_users'] = {
                'count': len(inactive_users),
                'users': [user['username'] for user in inactive_users],
                'description': '90일 이상 미활동 사용자',
                'details': inactive_users,
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본 1.2는 fix() 함수가 없고 자동 조치를 제공하지 않음
        return None
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본 1.2는 fix() 함수가 없고 자동 조치를 제공하지 않음
        return [{
            'item': 'manual_review',
            'status': 'info',
            'message': '[ⓘ MANUAL] 1명의 담당자가 여러 개의 IAM 계정을 사용하는지에 대해서는 수동 점검이 필요합니다.'
        }]