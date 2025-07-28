"""
1.8 액세스 키 라이프사이클 체커
액세스 키의 생성, 교체, 삭제 주기를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from ..base_checker import BaseChecker

class AccessKeyManagementChecker(BaseChecker):
    """1.8 액세스 키 라이프사이클 체커"""
    
    @property
    def item_code(self):
        return "1.8"
    
    @property 
    def item_name(self):
        return "액세스 키 라이프사이클"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            old_access_keys = []
            all_access_keys = []
            users_with_multiple_keys = []
            now = datetime.now(timezone.utc)
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    
                    try:
                        # 사용자의 액세스 키 목록 조회
                        keys_response = iam.list_access_keys(UserName=user_name)
                        user_keys = keys_response.get('AccessKeyMetadata', [])
                        
                        if len(user_keys) > 1:
                            users_with_multiple_keys.append({
                                'username': user_name,
                                'key_count': len(user_keys),
                                'keys': [key['AccessKeyId'] for key in user_keys]
                            })
                        
                        for key in user_keys:
                            key_age_days = (now - key['CreateDate']).days
                            all_access_keys.append(key_age_days)
                            
                            # 90일 이상 된 키 확인
                            if key_age_days > 90:
                                old_access_keys.append({
                                    'username': user_name,
                                    'access_key_id': key['AccessKeyId'],
                                    'age_days': key_age_days,
                                    'status': key['Status'],
                                    'create_date': key['CreateDate'].strftime('%Y-%m-%d')
                                })
                                
                    except Exception:
                        # 개별 사용자 키 조회 실패 시 건너뛰기
                        continue
            
            # 결과 분석
            has_issues = len(old_access_keys) > 0 or len(users_with_multiple_keys) > 0
            risk_level = self.calculate_risk_level(len(old_access_keys) + len(users_with_multiple_keys))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_access_keys': len(all_access_keys),
                'old_access_keys': old_access_keys,
                'old_keys_count': len(old_access_keys),
                'users_with_multiple_keys': users_with_multiple_keys,
                'multiple_keys_count': len(users_with_multiple_keys),
                'average_key_age': sum(all_access_keys) / len(all_access_keys) if all_access_keys else 0,
                'recommendation': "액세스 키는 90일마다 교체하고, 사용자당 1개의 활성 키만 유지하는 것을 권장합니다."
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
            old_count = result.get('old_keys_count', 0)
            multiple_count = result.get('multiple_keys_count', 0)
            issues = []
            if old_count > 0:
                issues.append(f"90일 이상 된 키 {old_count}개")
            if multiple_count > 0:
                issues.append(f"다중 키 보유 사용자 {multiple_count}명")
            return f"⚠️ 액세스 키 관리 이슈: {', '.join(issues)}"
        else:
            return "✅ 모든 액세스 키가 적절히 관리되고 있습니다."
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        fix_options = []
        
        old_keys = result.get('old_access_keys', [])
        if old_keys:
            fix_options.append({
                'id': 'deactivate_old_keys',
                'title': '오래된 액세스 키 비활성화',
                'description': f'{len(old_keys)}개의 90일 이상 된 액세스 키를 비활성화합니다.',
                'items': [{'id': f"{key['username']}:{key['access_key_id']}", 'name': key['access_key_id'], 'description': f"{key['username']} - {key['age_days']}일 경과"} for key in old_keys],
                'action_type': 'deactivate'
            })
        
        return fix_options if fix_options else None
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            results = []
            
            for fix_id, items in selected_items.items():
                if fix_id == 'deactivate_old_keys':
                    for item in items:
                        user_name, access_key_id = item['id'].split(':')
                        try:
                            iam.update_access_key(
                                UserName=user_name,
                                AccessKeyId=access_key_id,
                                Status='Inactive'
                            )
                            
                            results.append({
                                'item': access_key_id,
                                'status': 'success',
                                'message': f'{user_name}의 액세스 키 {access_key_id}가 비활성화되었습니다.'
                            })
                            
                        except ClientError as e:
                            results.append({
                                'item': access_key_id,
                                'status': 'error',
                                'message': f'{access_key_id} 비활성화 실패: {str(e)}'
                            })
            
            return results
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'조치 실행 중 오류가 발생했습니다: {str(e)}'
            }]