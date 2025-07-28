"""
1.3 IAM 사용자 계정 식별 관리 진단 (Flask용)
mainHub의 iam_identification_1_3.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError
from datetime import datetime

class IAMIdentificationChecker(BaseChecker):
    """1.3 IAM 사용자 계정 식별 관리 진단"""
    
    @property
    def item_code(self):
        return "1.3"
    
    @property 
    def item_name(self):
        return "IAM 사용자 계정 식별 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 모든 IAM 사용자가 식별을 위한 태그를 가지고 있는지 점검하고, 태그 없는 사용자 목록을 반환
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            untagged_users = []
            total_users = 0

            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # 사용자 태그 확인
                    tags_response = iam.list_user_tags(UserName=user_name)
                    tags = tags_response.get('Tags', [])
                    
                    if not tags:
                        untagged_users.append(user_name)

            # 위험도 계산
            untagged_count = len(untagged_users)
            risk_level = self.calculate_risk_level(
                untagged_count,
                1 if untagged_count > 0 else 0  # 태그 없는 사용자가 있으면 중간 위험도
            )

            return {
                "status": "success",
                "untagged_users": untagged_users,
                "untagged_count": untagged_count,
                "total_users": total_users,
                "risk_level": risk_level,
                "has_issues": untagged_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_users = result.get('total_users', 0)
        untagged_count = result.get('untagged_count', 0)
        
        if untagged_count > 0:
            return f"⚠️ 전체 {total_users}개 사용자 중 {untagged_count}개 사용자에게 식별 태그가 없습니다."
        else:
            return f"✅ 모든 {total_users}개 사용자가 식별 태그를 보유하고 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "사용자 통계": {
                "전체 사용자 수": result.get('total_users', 0),
                "태그 없는 사용자": result.get('untagged_count', 0),
                "recommendation": "모든 IAM 사용자는 식별을 위한 태그(이름, 이메일, 부서, 역할 등)를 보유해야 합니다."
            }
        }
        
        if result.get('untagged_users'):
            details["태그 없는 사용자 목록"] = {
                "users": result['untagged_users'],
                "recommendation": "해당 사용자들에게 Name, Email, Department, Role 등의 태그를 추가하세요."
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        untagged_users = result.get('untagged_users', [])
        
        if untagged_users:
            return [{
                "type": "add_identification_tags",
                "title": "식별 태그 추가",
                "description": f"{len(untagged_users)}개 사용자에게 식별용 태그를 추가합니다.",
                "items": [{"user": user, "action": "Name, Email, Department, Role 태그 추가"} 
                         for user in untagged_users],
                "severity": "medium",
                "form_fields": [
                    {"name": "tag_name", "type": "text", "label": "이름", "placeholder": "예: 홍길동"},
                    {"name": "tag_email", "type": "email", "label": "이메일", "placeholder": "예: hong@company.com"},
                    {"name": "tag_department", "type": "text", "label": "부서", "placeholder": "예: IT보안팀"},
                    {"name": "tag_role", "type": "text", "label": "역할", "placeholder": "예: 보안관리자"}
                ]
            }]
        
        return None
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            results = []
            
            for user_name in selected_items.get('untagged_users', []):
                try:
                    # 공통 태그 생성 (빈 값 제외)
                    tags = []
                    common_tags = selected_items.get('common_tags', {})
                    
                    for key, value in common_tags.items():
                        if value and value.strip():  # 빈 값이 아닌 경우에만 추가
                            tags.append({'Key': key, 'Value': value.strip()})
                    
                    # 기본 태그 추가 (생성일)
                    tags.append({
                        'Key': 'CreatedBy', 
                        'Value': 'WALB-SecurityAutomation'
                    })
                    tags.append({
                        'Key': 'TaggedDate', 
                        'Value': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    if tags:
                        iam.tag_user(UserName=user_name, Tags=tags)
                        results.append({
                            "user": user_name, 
                            "action": "태그 추가", 
                            "status": "success",
                            "details": f"{len(tags)}개 태그 추가됨"
                        })
                    else:
                        results.append({
                            "user": user_name, 
                            "action": "태그 추가", 
                            "status": "skipped",
                            "details": "추가할 태그 정보가 없음"
                        })
                        
                except ClientError as e:
                    results.append({
                        "user": user_name, 
                        "action": "태그 추가", 
                        "status": "error", 
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{"user": "전체", "action": "조치 실행", "status": "error", "error": str(e)}]