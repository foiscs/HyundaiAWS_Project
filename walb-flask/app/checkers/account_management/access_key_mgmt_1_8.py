"""
1.8 Access Key 관리 진단 (Flask용)
mainHub의 access_key_mgmt_1_8.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from datetime import datetime, timezone
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class AccessKeyManagement18(BaseChecker):
    """1.8 Access Key 관리 진단"""
    
    @property
    def item_code(self):
        return "1.8"
    
    @property 
    def item_name(self):
        return "Access Key 관리"
    
    def run_diagnosis(self):
        """
        진단 수행 - IAM 사용자의 Access Key 관리 상태 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            key_issues = []
            total_users = 0
            now = datetime.now(timezone.utc)
            
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # 사용자의 Access Key 조회
                    keys_response = iam.list_access_keys(UserName=user_name)
                    access_keys = keys_response.get('AccessKeyMetadata', [])
                    
                    for key in access_keys:
                        key_id = key['AccessKeyId']
                        create_date = key['CreateDate']
                        status = key['Status']
                        
                        # 키 생성일로부터 경과일 계산
                        age_days = (now - create_date).days
                        
                        # 문제 상황 체크
                        issues = []
                        
                        if age_days > 90:
                            issues.append(f"90일 이상 사용 ({age_days}일)")
                        
                        if status == 'Inactive':
                            issues.append("비활성 상태")
                        
                        # 마지막 사용일 확인
                        try:
                            last_used_info = iam.get_access_key_last_used(AccessKeyId=key_id)
                            last_used_date = last_used_info.get('AccessKeyLastUsed', {}).get('LastUsedDate')
                            
                            if last_used_date:
                                last_used_days = (now - last_used_date).days
                                if last_used_days > 30:
                                    issues.append(f"30일 이상 미사용 ({last_used_days}일)")
                            else:
                                issues.append("사용 이력 없음")
                        except ClientError:
                            issues.append("사용 이력 확인 불가")
                        
                        if issues:
                            key_issues.append({
                                'user_name': user_name,
                                'access_key_id': key_id,
                                'create_date': create_date.isoformat(),
                                'status': status,
                                'age_days': age_days,
                                'issues': issues
                            })
            
            # 위험도 계산
            issues_count = len(key_issues)
            risk_level = self.calculate_risk_level(
                issues_count,
                2 if any('90일 이상' in str(issue['issues']) for issue in key_issues) else 1
            )
            
            return {
                "status": "success",
                "key_issues": key_issues,
                "total_users": total_users,
                "issues_count": issues_count,
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
        total_users = result.get('total_users', 0)
        issues_count = result.get('issues_count', 0)
        
        if issues_count > 0:
            return f"⚠️ 전체 {total_users}개 사용자에서 {issues_count}개의 Access Key 관리 문제가 발견되었습니다."
        else:
            return f"✅ 모든 사용자의 Access Key가 적절히 관리되고 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "Access Key 관리 상태": {
                "검사한 사용자 수": result.get('total_users', 0),
                "문제가 있는 키": result.get('issues_count', 0),
                "recommendation": "Access Key는 정기적으로 교체하고 사용하지 않는 키는 비활성화하세요."
            }
        }
        
        if result.get('key_issues'):
            details["문제가 있는 Access Key"] = {}
            for issue in result['key_issues']:
                key_info = f"{issue['user_name']}/{issue['access_key_id'][:8]}***"
                details["문제가 있는 Access Key"][key_info] = {
                    "생성일": issue['create_date'],
                    "상태": issue['status'],
                    "경과일": f"{issue['age_days']}일",
                    "문제점": issue['issues']
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        key_issues = result.get('key_issues', [])
        
        if key_issues:
            return [{
                "type": "rotate_old_keys",
                "title": "오래된 Access Key 교체",
                "description": f"{len(key_issues)}개의 문제가 있는 Access Key를 비활성화합니다.",
                "items": [{"user": issue['user_name'], 
                          "key_id": issue['access_key_id'][:8] + "***",
                          "issues": ", ".join(issue['issues']),
                          "action": "Key 비활성화"} 
                         for issue in key_issues],
                "severity": "medium"
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
            keys_to_deactivate = selected_items.get('old_keys', [])
            
            for key_info in keys_to_deactivate:
                try:
                    iam.update_access_key(
                        UserName=key_info['user_name'],
                        AccessKeyId=key_info['access_key_id'],
                        Status='Inactive'
                    )
                    results.append({
                        "user": key_info['user_name'],
                        "key_id": key_info['access_key_id'][:8] + "***",
                        "action": "Access Key 비활성화",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "user": key_info['user_name'],
                        "key_id": key_info['access_key_id'][:8] + "***",
                        "action": "Access Key 비활성화",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "전체",
                "action": "Access Key 관리",
                "status": "error",
                "error": str(e)
            }]