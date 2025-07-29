"""
1.1 사용자 계정 관리 체커
관리자 계정과 테스트 계정을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import re
from ..base_checker import BaseChecker

class UserAccountChecker(BaseChecker):
    """1.1 사용자 계정 관리 체커"""
    
    @property
    def item_code(self):
        return "1.1"
    
    @property 
    def item_name(self):
        return "사용자 계정 관리"
    
    def is_test_user(self, user_name):
        """테스트 사용자 여부 판단"""
        return bool(re.match(r'^(test|tmp|guest|retired|퇴직|미사용)', user_name, re.IGNORECASE))
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            now = datetime.now(timezone.utc)
            admin_users = set()
            test_users = set()
            all_users = []
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    name = user['UserName']
                    all_users.append(name)
                    is_admin = False
                    
                    # 테스트 사용자 확인
                    if self.is_test_user(name):
                        test_users.add(name)
                    
                    # 직접 연결된 관리자 정책 확인
                    user_policies = iam.list_attached_user_policies(UserName=name)['AttachedPolicies']
                    if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in user_policies):
                        is_admin = True
                    
                    # 그룹을 통한 관리자 정책 확인
                    if not is_admin:
                        groups = iam.list_groups_for_user(UserName=name)['Groups']
                        for g in groups:
                            group_policies = iam.list_attached_group_policies(GroupName=g['GroupName'])['AttachedPolicies']
                            if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in group_policies):
                                is_admin = True
                                break
                    
                    if is_admin:
                        admin_users.add(name)
            
            # 결과 분석
            has_issues = len(test_users) > 0
            risk_level = self.calculate_risk_level(len(test_users))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_users': len(all_users),
                'admin_users': list(admin_users),
                'admin_count': len(admin_users),
                'test_users': list(test_users),
                'test_count': len(test_users),
                'recommendation': "테스트/임시 계정은 정기적으로 정리하여 보안을 강화하세요."
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
        admin_count = result.get('admin_count', 0)
        test_count = result.get('test_count', 0)
        admin_users = result.get('admin_users', [])
        test_users = result.get('test_users', [])
        
        summary = f"[RESULT] IAM 관리자: {admin_count}명"
        if admin_count > 0:
            summary += f"\n  └ {', '.join(admin_users)}"
        else:
            summary += "\n  └ 없음"
            
        summary += f"\n\n[RESULT] 테스트/임시 계정: {test_count}개"
        if test_count > 0:
            summary += f"\n  └ {', '.join(test_users)}"
        else:
            summary += "\n  └ 없음"
            
        return summary
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_users': {
                'count': result.get('total_users', 0),
                'description': '전체 IAM 사용자 수'
            },
            'admin_users': {
                'count': result.get('admin_count', 0),
                'users': result.get('admin_users', []),
                'description': '관리자 권한을 가진 사용자'
            }
        }
        
        if result.get('has_issues'):
            details['test_users'] = {
                'count': result.get('test_count', 0),
                'users': result.get('test_users', []),
                'description': '테스트/임시 계정',
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        fix_options = []
        
        # 관리자 권한 제거 옵션
        admin_users = result.get('admin_users', [])
        if admin_users:
            fix_options.append({
                'id': 'remove_admin_access',
                'title': '관리자 권한 제거',
                'description': f'{len(admin_users)}명의 관리자 권한을 제거합니다.',
                'items': [{'id': user, 'name': user, 'description': f'{user} 사용자의 관리자 권한'} for user in admin_users],
                'action_type': 'remove_policy'
            })
        
        # 테스트 계정 콘솔 로그인 비활성화 옵션
        test_users = result.get('test_users', [])
        if test_users:
            fix_options.append({
                'id': 'disable_test_console',
                'title': '테스트 계정 콘솔 로그인 비활성화',
                'description': f'{len(test_users)}개의 테스트/임시 계정의 콘솔 로그인을 비활성화합니다.',
                'items': [{'id': user, 'name': user, 'description': f'{user} 테스트 계정'} for user in test_users],
                'action_type': 'disable_console'
            })
        
        return fix_options if fix_options else None
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            results = []
            
            for fix_id, items in selected_items.items():
                if fix_id == 'remove_admin_access':
                    # 관리자 권한 제거 (원본 로직)
                    for item in items:
                        user_name = item['id']
                        try:
                            iam.detach_user_policy(
                                UserName=user_name, 
                                PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
                            )
                            results.append({
                                'item': user_name,
                                'status': 'success',
                                'message': f'✔ 관리자 권한 제거 완료: {user_name}'
                            })
                        except ClientError as e:
                            results.append({
                                'item': user_name,
                                'status': 'error',
                                'message': f'✖ 실패: {str(e)}'
                            })
                
                elif fix_id == 'disable_test_console':
                    # 테스트 계정 콘솔 로그인 비활성화 (원본 로직)
                    for item in items:
                        user_name = item['id']
                        try:
                            iam.delete_login_profile(UserName=user_name)
                            results.append({
                                'item': user_name,
                                'status': 'success',
                                'message': f'✔ 콘솔 로그인 제거 완료: {user_name}'
                            })
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'NoSuchEntity':
                                results.append({
                                    'item': user_name,
                                    'status': 'info',
                                    'message': f'ℹ 이미 비활성화됨: {user_name}'
                                })
                            else:
                                results.append({
                                    'item': user_name,
                                    'status': 'error',
                                    'message': f'✖ 실패: {str(e)}'
                                })
            
            return results
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'조치 실행 중 오류가 발생했습니다: {str(e)}'
            }]