"""
2.3 기타 서비스 정책 관리 진단 (Flask용)
mainHub의 other_service_policy_2_3.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class OtherServicePolicyChecker(BaseChecker):
    """2.3 기타 서비스 정책 관리 진단"""
    
    @property
    def item_code(self):
        return "2.3"
    
    @property 
    def item_name(self):
        return "기타 서비스 정책 관리"
    
    def __init__(self, session=None):
        super().__init__(session)
        # 점검 대상 기타 서비스 과도한 권한 정책들
        self.overly_permissive_policies = {
            "arn:aws:iam::aws:policy/AmazonSNSFullAccess": "SNS",
            "arn:aws:iam::aws:policy/AmazonSQSFullAccess": "SQS", 
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess": "Lambda",
            "arn:aws:iam::aws:policy/CloudWatchFullAccess": "CloudWatch",
            "arn:aws:iam::aws:policy/AWSCloudTrail_FullAccess": "CloudTrail",
            "arn:aws:iam::aws:policy/AmazonKinesisFullAccess": "Kinesis",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess": "DynamoDB",
            "arn:aws:iam::aws:policy/SecretsManagerReadWrite": "Secrets Manager"
        }
    
    def run_diagnosis(self):
        """
        진단 수행
        - 기타 주요 서비스에 대해 과도한 권한(*FullAccess)이 부여되었는지 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            findings = []
            
            for policy_arn, service_name in self.overly_permissive_policies.items():
                try:
                    paginator = iam.get_paginator('list_entities_for_policy')
                    for page in paginator.paginate(PolicyArn=policy_arn):
                        # 사용자에게 연결된 정책 확인
                        for user in page.get('PolicyUsers', []):
                            findings.append({
                                'type': 'user',
                                'name': user['UserName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                        
                        # 그룹에 연결된 정책 확인
                        for group in page.get('PolicyGroups', []):
                            findings.append({
                                'type': 'group',
                                'name': group['GroupName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                        
                        # 역할에 연결된 정책 확인
                        for role in page.get('PolicyRoles', []):
                            findings.append({
                                'type': 'role',
                                'name': role['RoleName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                            
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        continue
                    else:
                        raise e

            # 위험도 계산
            finding_count = len(findings)
            risk_level = self.calculate_risk_level(
                finding_count,
                3 if finding_count > 5 else 2 if finding_count > 0 else 1
            )

            return {
                "status": "success",
                "findings": findings,
                "finding_count": finding_count,
                "services_affected": list(set([f['service'] for f in findings])),
                "risk_level": risk_level,
                "has_issues": finding_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"기타 서비스 정책 정보를 가져오는 중 오류 발생: {str(e)}"
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        finding_count = result.get('finding_count', 0)
        services_affected = result.get('services_affected', [])
        
        if finding_count > 0:
            return f"⚠️ 기타 서비스에서 {finding_count}개의 과도한 권한이 발견되었습니다. (영향 서비스: {len(services_affected)}개)"
        else:
            return "✅ 기타 서비스에 과도한 권한이 부여된 주체가 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "기타 서비스 권한 검사 결과": {
                "과도한 권한 발견": result.get('finding_count', 0),
                "영향받는 기타 서비스": result.get('services_affected', []),
                "recommendation": "FullAccess 정책 대신 업무에 필요한 최소 권한만 부여하세요."
            }
        }
        
        if result.get('findings'):
            details["과도한 기타 서비스 권한 주체"] = {}
            for finding in result['findings']:
                entity_key = f"{finding['type']}: {finding['name']}"
                details["과도한 기타 서비스 권한 주체"][entity_key] = {
                    "정책": finding['policy'],
                    "서비스": finding['service'],
                    "정책 ARN": finding['policy_arn']
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        return [{
            "type": "manual_service_review",
            "title": "기타 서비스 권한 수동 검토",
            "description": "서비스 권한 변경은 애플리케이션 동작에 영향을 줄 수 있어 수동 검토가 필요합니다.",
            "items": [{"entity": f"{f['type']}: {f['name']}", 
                      "policy": f['policy'], 
                      "service": f['service'],
                      "action": "서비스 권한 검토"} 
                     for f in result.get('findings', [])],
            "severity": "medium",
            "manual_only": True
        }]
    
    def execute_fix(self, selected_items):
        """조치 실행 - 자동 조치 제한"""
        return [{
            "entity": "기타 서비스 권한",
            "action": "자동 조치 제한",
            "status": "manual_required",
            "message": "서비스 권한 변경은 애플리케이션 동작에 영향을 줄 수 있어 수동 조치만 가능합니다."
        }]