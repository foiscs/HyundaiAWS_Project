"""
2.1 인스턴스 서비스 정책 관리 진단 (Flask용)
mainHub의 instance_service_policy_2_1.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class InstanceServicePolicyChecker(BaseChecker):
    """2.1 인스턴스 서비스 정책 관리 진단"""
    
    @property
    def item_code(self):
        return "2.1"
    
    @property 
    def item_name(self):
        return "인스턴스 서비스 정책 관리"
    
    def __init__(self, session=None):
        super().__init__(session)
        # 점검 대상 과도한 권한 정책들
        self.overly_permissive_policies = {
            "arn:aws:iam::aws:policy/AmazonEC2FullAccess": "EC2",
            "arn:aws:iam::aws:policy/AmazonECS_FullAccess": "ECS", 
            "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess": "ECR",
            "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy": "EKS",
            "arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess": "EFS",
            "arn:aws:iam::aws:policy/AmazonRDSFullAccess": "RDS",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess": "S3"
        }
    
    def run_diagnosis(self):
        """
        진단 수행
        - 주요 인스턴스 서비스에 대해 과도한 권한(*FullAccess)이 부여되었는지 점검
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
                "error_message": f"IAM 정책 정보를 가져오는 중 오류 발생: {str(e)}"
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        finding_count = result.get('finding_count', 0)
        services_affected = result.get('services_affected', [])
        
        if finding_count > 0:
            return f"⚠️ {finding_count}개의 과도한 권한이 발견되었습니다. (영향 서비스: {len(services_affected)}개)"
        else:
            return "✅ 인스턴스 관련 서비스에 과도한 권한이 부여된 주체가 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "권한 검사 결과": {
                "과도한 권한 발견": result.get('finding_count', 0),
                "영향받는 서비스": result.get('services_affected', []),
                "recommendation": "FullAccess 정책 대신 최소 권한 원칙에 따른 세분화된 정책을 사용하세요."
            }
        }
        
        if result.get('findings'):
            details["과도한 권한 주체"] = {}
            for finding in result['findings']:
                entity_key = f"{finding['type']}: {finding['name']}"
                details["과도한 권한 주체"][entity_key] = {
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
            "type": "manual_review_required",
            "title": "수동 권한 검토 필요",
            "description": "권한 변경은 운영에 큰 영향을 줄 수 있어 수동 검토가 필요합니다.",
            "items": [{"entity": f"{f['type']}: {f['name']}", 
                      "policy": f['policy'], 
                      "service": f['service'],
                      "action": "수동 권한 검토"} 
                     for f in result.get('findings', [])],
            "severity": "high",
            "manual_only": True,
            "guidance": {
                "steps": [
                    "IAM Access Analyzer로 실제 사용 권한 분석",
                    "최소 권한 원칙에 따른 맞춤형 정책 생성",
                    "테스트 환경에서 새 정책 검증",
                    "단계적으로 과도한 정책 제거"
                ],
                "cli_commands": [
                    f"aws iam detach-{f['type']}-policy --{f['type']}-name {f['name']} --policy-arn {f['policy_arn']}"
                    for f in result.get('findings', [])[:5]
                ],
                "console_links": [
                    "IAM Access Analyzer: https://console.aws.amazon.com/access-analyzer/",
                    "IAM 정책 시뮬레이터: https://policysim.aws.amazon.com/",
                    "IAM 콘솔: https://console.aws.amazon.com/iam/"
                ]
            }
        }]
    
    def execute_fix(self, selected_items):
        """조치 실행 - 자동 조치 제한"""
        return [{
            "entity": "보안 정책",
            "action": "자동 조치 제한",
            "status": "manual_required",
            "message": "권한 변경은 운영에 큰 영향을 줄 수 있어 수동 조치만 가능합니다. IAM Access Analyzer를 사용하여 안전하게 조치하세요."
        }]