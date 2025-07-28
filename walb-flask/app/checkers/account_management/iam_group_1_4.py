"""
1.4 IAM 그룹 사용자 계정 관리 진단 (Flask용)
mainHub의 iam_group_1_4.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class IAMGroupChecker(BaseChecker):
    """1.4 IAM 그룹 사용자 계정 관리 진단"""
    
    @property
    def item_code(self):
        return "1.4"
    
    @property 
    def item_name(self):
        return "IAM 그룹 사용자 계정 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 모든 IAM 사용자가 하나 이상의 그룹에 속해 있는지 점검하고, 미소속 사용자 목록을 반환
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            users_not_in_group = []
            total_users = 0

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # 사용자가 속한 그룹 확인
                    groups_response = iam.list_groups_for_user(UserName=user_name)
                    if not groups_response.get('Groups'):
                        users_not_in_group.append(user_name)

            # 위험도 계산
            unassigned_count = len(users_not_in_group)
            risk_level = self.calculate_risk_level(
                unassigned_count,
                2 if unassigned_count > 3 else 1  # 많은 미소속 사용자는 더 심각
            )

            return {
                "status": "success",
                "users_not_in_group": users_not_in_group,
                "unassigned_count": unassigned_count,
                "total_users": total_users,
                "risk_level": risk_level,
                "has_issues": unassigned_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_users = result.get('total_users', 0)
        unassigned_count = result.get('unassigned_count', 0)
        
        if unassigned_count > 0:
            return f"⚠️ 전체 {total_users}개 사용자 중 {unassigned_count}개가 IAM 그룹에 속하지 않습니다."
        else:
            return f"✅ 모든 {total_users}개 사용자가 IAM 그룹에 속해 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "사용자 통계": {
                "전체 사용자 수": result.get('total_users', 0),
                "그룹 미소속 사용자": result.get('unassigned_count', 0),
                "recommendation": "모든 IAM 사용자는 적절한 권한 관리를 위해 그룹에 속해야 합니다."
            }
        }
        
        if result.get('users_not_in_group'):
            details["그룹 미소속 사용자 목록"] = {
                "users": result['users_not_in_group'],
                "recommendation": "해당 사용자들을 적절한 IAM 그룹에 할당하여 권한을 관리하세요."
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        users_not_in_group = result.get('users_not_in_group', [])
        
        if users_not_in_group:
            return [{
                "type": "assign_to_groups",
                "title": "IAM 그룹 할당",
                "description": f"{len(users_not_in_group)}개 사용자를 IAM 그룹에 할당합니다.",
                "items": [{"user": user, "action": "IAM 그룹에 할당"} 
                         for user in users_not_in_group],
                "severity": "medium",
                "requires_group_selection": True
            }]
        
        return None
    
    def get_available_groups(self):
        """사용 가능한 IAM 그룹 목록 반환"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            groups_response = iam.list_groups()
            return [group['GroupName'] for group in groups_response['Groups']]
            
        except ClientError as e:
            return []
    
    def create_group(self, group_name):
        """새 IAM 그룹 생성"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            iam.create_group(GroupName=group_name)
            return {"status": "success", "message": f"그룹 '{group_name}' 생성 완료"}
            
        except ClientError as e:
            return {"status": "error", "message": str(e)}
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            results = []
            user_group_assignments = selected_items.get('user_group_assignments', {})
            
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