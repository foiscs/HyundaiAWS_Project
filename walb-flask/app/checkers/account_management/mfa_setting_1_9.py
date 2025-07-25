"""
1.9 MFA 설정 진단 (Flask용)
mainHub의 mfa_setting_1_9.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class MFASettingChecker(BaseChecker):
    """1.9 MFA 설정 진단"""
    
    @property
    def item_code(self):
        return "1.9"
    
    @property 
    def item_name(self):
        return "MFA 설정"
    
    def run_diagnosis(self):
        """
        진단 수행 - IAM 사용자의 MFA 설정 상태 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
                
            users_without_mfa = []
            total_users = 0
            
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    total_users += 1
                    user_name = user['UserName']
                    
                    # MFA 디바이스 확인
                    mfa_devices = iam.list_mfa_devices(UserName=user_name)
                    if not mfa_devices.get('MFADevices'):
                        users_without_mfa.append(user_name)
            
            # 위험도 계산
            mfa_missing_count = len(users_without_mfa)
            risk_level = self.calculate_risk_level(
                mfa_missing_count,
                3  # MFA 미설정은 높은 위험도
            )
            
            return {
                "status": "success",
                "users_without_mfa": users_without_mfa,
                "mfa_missing_count": mfa_missing_count,
                "total_users": total_users,
                "risk_level": risk_level,
                "has_issues": mfa_missing_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_users = result.get('total_users', 0)
        mfa_missing_count = result.get('mfa_missing_count', 0)
        
        if mfa_missing_count > 0:
            return f"⚠️ 전체 {total_users}개 사용자 중 {mfa_missing_count}개가 MFA를 설정하지 않았습니다."
        else:
            return f"✅ 모든 {total_users}개 사용자가 MFA를 설정했습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "MFA 설정 통계": {
                "전체 사용자 수": result.get('total_users', 0),
                "MFA 미설정 사용자": result.get('mfa_missing_count', 0),
                "recommendation": "모든 IAM 사용자는 보안을 위해 MFA(다단계 인증)를 설정해야 합니다."
            }
        }
        
        if result.get('users_without_mfa'):
            details["MFA 미설정 사용자 목록"] = {
                "users": result['users_without_mfa'],
                "recommendation": "해당 사용자들에게 MFA 디바이스를 할당하고 활성화하세요."
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        users_without_mfa = result.get('users_without_mfa', [])
        
        if users_without_mfa:
            return [{
                "type": "enforce_mfa_policy",
                "title": "MFA 강제 정책 적용",
                "description": f"{len(users_without_mfa)}개 사용자에게 MFA 강제 정책을 적용합니다.",
                "items": [{"user": user, "action": "MFA 강제 정책 적용"} 
                         for user in users_without_mfa],
                "severity": "high"
            }]
        
        return None
    
    def execute_fix(self, selected_items):
        """조치 실행 - MFA 강제 정책 생성 및 적용"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            results = []
            
            # MFA 강제 정책 생성
            mfa_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Deny",
                        "NotAction": [
                            "iam:CreateVirtualMFADevice",
                            "iam:EnableMFADevice",
                            "iam:GetUser",
                            "iam:ListMFADevices",
                            "iam:ListVirtualMFADevices",
                            "iam:ResyncMFADevice",
                            "sts:GetSessionToken"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "BoolIfExists": {
                                "aws:MultiFactorAuthPresent": "false"
                            }
                        }
                    }
                ]
            }
            
            policy_name = "WALB-ForceMFA-Policy"
            
            try:
                # 정책이 이미 존재하는지 확인
                iam.get_policy(PolicyArn=f"arn:aws:iam::{iam.get_user()['User']['Arn'].split(':')[4]}:policy/{policy_name}")
                policy_exists = True
            except ClientError:
                policy_exists = False
            
            if not policy_exists:
                # 정책 생성
                try:
                    import json
                    iam.create_policy(
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(mfa_policy),
                        Description="WALB 보안 자동화 - MFA 강제 정책"
                    )
                    results.append({
                        "action": "MFA 강제 정책 생성",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "action": "MFA 강제 정책 생성",
                        "status": "error",
                        "error": str(e)
                    })
            
            # 사용자에게 정책 적용
            for user in selected_items.get('users_without_mfa', []):
                try:
                    iam.attach_user_policy(
                        UserName=user,
                        PolicyArn=f"arn:aws:iam::{iam.get_user()['User']['Arn'].split(':')[4]}:policy/{policy_name}"
                    )
                    results.append({
                        "user": user,
                        "action": "MFA 강제 정책 적용",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "user": user,
                        "action": "MFA 강제 정책 적용",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "user": "전체",
                "action": "MFA 정책 적용",
                "status": "error",
                "error": str(e)
            }]