"""
1.1 사용자 계정 관리 진단
"""
import boto3
from botocore.exceptions import ClientError
import re
from ..base_checker import BaseChecker

class UserAccountChecker(BaseChecker):
    """1.1 사용자 계정 관리 진단"""
    
    @property
    def item_code(self):
        return "1.1"
    
    @property 
    def item_name(self):
        return "사용자 계정 관리"
    
    def is_test_user(self, user_name):
        """테스트/임시 사용자 판별"""
        return bool(re.match(r'^(test|tmp|guest|retired|퇴직|미사용)', user_name, re.IGNORECASE))
    
    def run_diagnosis(self):
        """진단 수행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            admin_users = set()
            test_users = set()

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    name = user['UserName']
                    is_admin = False

                    if self.is_test_user(name):
                        test_users.add(name)

                    user_policies = iam.list_attached_user_policies(UserName=name)['AttachedPolicies']
                    if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in user_policies):
                        is_admin = True

                    if not is_admin:
                        groups = iam.list_groups_for_user(UserName=name)['Groups']
                        for g in groups:
                            group_policies = iam.list_attached_group_policies(GroupName=g['GroupName'])['AttachedPolicies']
                            if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in group_policies):
                                is_admin = True
                                break

                    if is_admin:
                        admin_users.add(name)

            admin_count = len(admin_users)
            test_count = len(test_users)
            
            # 위험도 계산
            risk_level = self.calculate_risk_level(
                test_count + max(0, admin_count - 2),  # 테스트 계정 + 초과 관리자
                2 if test_count > 0 else 1  # 테스트 계정은 더 심각
            )

            return {
                "status": "success",
                "admin_users": list(admin_users),
                "test_users": list(test_users),
                "admin_count": admin_count,
                "test_count": test_count,
                "risk_level": risk_level,
                "has_issues": admin_count > 2 or test_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            results = []
            
            # 관리자 권한 제거
            for user in selected_items.get('admin_users', []):
                success = False
                error_msgs = []
                
                # 1. 직접 연결된 정책 제거 시도
                try:
                    iam.detach_user_policy(UserName=user, PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
                    success = True
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchEntity':
                        error_msgs.append(f"직접 정책 제거 실패: {str(e)}")
                
                # 2. 그룹에서 사용자 제거 시도 (관리자 권한을 가진 그룹에서만)
                try:
                    groups = iam.list_groups_for_user(UserName=user)['Groups']
                    for group in groups:
                        group_name = group['GroupName']
                        group_policies = iam.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
                        
                        # AdministratorAccess를 가진 그룹에서 사용자 제거
                        if any(p['PolicyArn'].endswith('/AdministratorAccess') for p in group_policies):
                            iam.remove_user_from_group(UserName=user, GroupName=group_name)
                            success = True
                            
                except ClientError as e:
                    error_msgs.append(f"그룹 제거 실패: {str(e)}")
                
                # 결과 기록
                if success:
                    results.append({"user": user, "action": "관리자 권한 제거", "status": "success"})
                else:
                    results.append({"user": user, "action": "관리자 권한 제거", "status": "error", "error": "; ".join(error_msgs)})
            
            # 테스트 계정 콘솔 로그인 비활성화
            for user in selected_items.get('test_users', []):
                try:
                    iam.delete_login_profile(UserName=user)
                    results.append({"user": user, "action": "콘솔 로그인 비활성화", "status": "success"})
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        results.append({"user": user, "action": "콘솔 로그인 비활성화", "status": "already_done"})
                    else:
                        results.append({"user": user, "action": "콘솔 로그인 비활성화", "status": "error", "error": str(e)})
            
            return results
            
        except Exception as e:
            return [{"user": "전체", "action": "조치 실행", "status": "error", "error": str(e)}]