"""
2.2 네트워크 서비스 정책 체커
네트워크 서비스에 대한 과도한 권한 관리를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class NetworkServicePolicyChecker(BaseChecker):
    """2.2 네트워크 서비스 정책 체커"""
    
    @property
    def item_code(self):
        return "2.2"
    
    @property 
    def item_name(self):
        return "네트워크 서비스 정책 관리"
    
    def run_diagnosis(self):
        """진단 실행 - 원본 2.2 로직 그대로 구현"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            # 원본 로직: 과도한 권한 정책 목록
            overly_permissive_policies = {
                "arn:aws:iam::aws:policy/AmazonVPCFullAccess": "VPC",
                "arn:aws:iam::aws:policy/AmazonRoute53FullAccess": "Route 53",
                "arn:aws:iam::aws:policy/AWSDirectConnect_FullAccess": "Direct Connect",
                "arn:aws:iam::aws:policy/CloudFrontFullAccess": "CloudFront",
                "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator": "API Gateway",
                "arn:aws:iam::aws:policy/AWSAppMeshFullAccess": "App Mesh",
                "arn:aws:iam::aws:policy/AWSCloudMapFullAccess": "Cloud Map"
            }
            findings = []
            
            try:
                for policy_arn, service_name in overly_permissive_policies.items():
                    try:
                        paginator = iam.get_paginator('list_entities_for_policy')
                        for page in paginator.paginate(PolicyArn=policy_arn):
                            for user in page.get('PolicyUsers', []):
                                findings.append({
                                    'type': 'user', 
                                    'name': user['UserName'], 
                                    'policy': policy_arn.split('/')[-1],
                                    'service': service_name,
                                    'policy_arn': policy_arn
                                })
                            for group in page.get('PolicyGroups', []):
                                findings.append({
                                    'type': 'group', 
                                    'name': group['GroupName'], 
                                    'policy': policy_arn.split('/')[-1],
                                    'service': service_name,
                                    'policy_arn': policy_arn
                                })
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
                
                # 결과 분석
                has_issues = len(findings) > 0
                risk_level = self.calculate_risk_level(len(findings))
                
                return {
                    'status': 'success',
                    'has_issues': has_issues,
                    'risk_level': risk_level,
                    'findings': findings,
                    'findings_count': len(findings),
                    'checked_policies': list(overly_permissive_policies.keys()),
                    'recommendation': "네트워크 관련 서비스에 과도한 권한(*FullAccess)이 부여되지 않도록 최소 권한 원칙을 적용하세요."
                }
                
            except ClientError as e:
                return {
                    'status': 'error',
                    'error_message': f'IAM 정책 정보를 가져오는 중 오류 발생: {str(e)}'
                }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        findings_count = result.get('findings_count', 0)
        
        if findings_count > 0:
            return f"[⚠ WARNING] 2.2 네트워크 관련 서비스에 과도한 권한이 부여되었습니다 ({findings_count}건)."
        else:
            return "[✓ COMPLIANT] 2.2 네트워크 관련 서비스에 과도한 권한이 부여된 주체가 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'checked_policies_count': len(result.get('checked_policies', [])),
            'findings_count': result.get('findings_count', 0)
        }
        
        findings = result.get('findings', [])
        if findings:
            details['findings'] = []
            for f in findings:
                details['findings'].append({
                    'entity_type': f['type'].capitalize(),
                    'entity_name': f['name'],
                    'policy_name': f['policy'],
                    'service': f['service'],
                    'description': f"{f['type'].capitalize()} '{f['name']}'에 '{f['policy']}' 정책 연결됨"
                })
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본 2.2는 권한 변경이 위험하므로 자동 조치 없음
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 2.2 fix() 함수 내용"""
        if not result.get('has_issues'):
            return None
        
        findings = result.get('findings', [])
        if not findings:
            return None
        
        # 원본 fix() 함수의 내용을 그대로 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 2.2 과도한 권한 정책 조치',
                'content': '과도한 권한 정책 조치는 운영에 큰 영향을 줄 수 있어 자동화되지 않습니다.'
            },
            {
                'type': 'info',
                'title': '수동 조치 가이드',
                'content': '아래 가이드에 따라 수동으로 조치하세요.'
            },
            {
                'type': 'step',
                'title': '1. [권장] AWS IAM Access Analyzer 사용',
                'content': 'AWS IAM Access Analyzer를 사용하여 실제 사용된 권한을 기반으로 세분화된 정책을 생성합니다.'
            },
            {
                'type': 'step',
                'title': '2. 새 정책 연결',
                'content': '생성된 새 정책을 해당 주체(사용자/그룹/역할)에 연결합니다.'
            },
            {
                'type': 'step',
                'title': '3. 기존 정책 분리',
                'content': '충분한 테스트 후, 아래 명령어를 참고하여 기존의 과도한 정책을 분리합니다.'
            }
        ]
        
        # CLI 명령어 추가
        cli_commands = []
        for f in findings:
            policy_arn = f"arn:aws:iam::aws:policy/{f['policy']}"
            if f['type'] == 'user':
                cli_commands.append(f"aws iam detach-user-policy --user-name {f['name']} --policy-arn {policy_arn}")
            elif f['type'] == 'group':
                cli_commands.append(f"aws iam detach-group-policy --group-name {f['name']} --policy-arn {policy_arn}")
            elif f['type'] == 'role':
                cli_commands.append(f"aws iam detach-role-policy --role-name {f['name']} --policy-arn {policy_arn}")
        
        if cli_commands:
            guide_steps.append({
                'type': 'commands',
                'title': 'AWS CLI 명령어 예시',
                'content': cli_commands
            })
        
        return {
            'title': '2.2 네트워크 서비스 정책 수동 조치 가이드',
            'description': '원본 팀원이 작성한 수동 조치 절차를 따라 권한을 안전하게 조정하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본 2.2는 권한 변경이 위험하므로 수동 조치 가이드만 제공
        return [{
            'item': 'manual_fix_only',
            'status': 'info',
            'message': '[FIX] 2.2 과도한 권한 정책 조치는 운영에 큰 영향을 줄 수 있어 자동화되지 않습니다.'
        }, {
            'item': 'fix_guide_1',
            'status': 'info',
            'message': '1. [권장] AWS IAM Access Analyzer를 사용하여 실제 사용된 권한을 기반으로 세분화된 정책을 생성합니다.'
        }, {
            'item': 'fix_guide_2',
            'status': 'info',
            'message': '2. 생성된 새 정책을 해당 주체(사용자/그룹/역할)에 연결합니다.'
        }, {
            'item': 'fix_guide_3',
            'status': 'info',
            'message': '3. 충분한 테스트 후, AWS CLI를 사용하여 기존의 과도한 정책을 분리합니다.'
        }]