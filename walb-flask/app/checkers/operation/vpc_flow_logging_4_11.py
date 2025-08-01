"""
[4.11] VPC 플로우 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_11_vpc_flow_logging.py
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class VpcFlowLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.11"
    
    @property 
    def item_name(self):
        return "VPC 플로우 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.11] VPC 플로우 로깅 설정 점검
        - 모든 VPC에서 Flow Logs가 활성화되어 있는지 확인
        """
        print("[INFO] 4.11 VPC 플로우 로깅 설정 체크 중...")
        ec2 = self.session.client('ec2')

        try:
            all_vpcs = {vpc['VpcId'] for vpc in ec2.describe_vpcs()['Vpcs']}
            active_logs = {f['ResourceId'] for f in ec2.describe_flow_logs()['FlowLogs'] if f['FlowLogStatus'] == 'ACTIVE'}
            vpcs_without_logs = list(all_vpcs - active_logs)

            if not vpcs_without_logs:
                print("[✓ COMPLIANT] 4.11 모든 VPC에 Flow Logs가 활성화되어 있습니다.")
                has_issues = False
                message = "모든 VPC에 Flow Logs가 활성화되어 있습니다."
            else:
                print(f"[⚠ WARNING] 4.11 Flow Logs가 비활성화된 VPC가 존재합니다 ({len(vpcs_without_logs)}개).")
                print(f"  ├─ 해당 VPC: {', '.join(vpcs_without_logs)}")
                has_issues = True
                message = f"Flow Logs가 비활성화된 VPC {len(vpcs_without_logs)}개 발견"

            risk_level = self.calculate_risk_level(len(vpcs_without_logs))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': message,
                'vpcs_without_logs': vpcs_without_logs,
                'all_vpcs': list(all_vpcs),
                'summary': f"Flow Logs 미설정 VPC {len(vpcs_without_logs)}개" if has_issues else "모든 VPC에 Flow Logs가 활성화되어 있습니다.",
                'details': {
                    'total_vpcs': len(all_vpcs),
                    'vpcs_without_logs_count': len(vpcs_without_logs),
                    'vpcs_with_logs_count': len(all_vpcs) - len(vpcs_without_logs)
                }
            }

        except ClientError as e:
            print(f"[ERROR] VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.11] VPC Flow Logs 설정 조치
        - 각 VPC에 대해 별도 로그 그룹을 생성하고, 공통 IAM 역할을 사용
        """
        if not selected_items:
            return [{'item': 'no_selection', 'status': 'info', 'message': '선택된 항목이 없습니다.'}]

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('vpcs_without_logs'):
            return [{'item': 'no_action_needed', 'status': 'info', 'message': 'VPC Flow Logs 조치가 필요한 항목이 없습니다.'}]

        vpcs_without_logs = diagnosis_result['vpcs_without_logs']
        results = []

        print("[FIX] 4.11 VPC Flow Logs 설정 조치를 시작합니다.")
        print("→ 각 VPC에 대해 별도 로그 그룹을 생성하고, 공통 IAM 역할을 사용합니다.\n")

        ec2 = self.session.client('ec2')
        iam_role_arn = self._get_or_create_common_iam_role()
        if not iam_role_arn:
            print("     [ERROR] IAM 역할 생성 실패로 인해 조치를 중단합니다.")
            return [{
                'item': 'system',
                'status': 'error',
                'message': 'IAM 역할 생성 실패로 인해 조치를 중단했습니다.'
            }]

        for vpc_id in vpcs_without_logs:
            # 선택된 항목인지 확인
            if any(vpc_id in str(item) for item in selected_items.values() for item in item):
                log_group_name = f"/vpc/flowlogs/{vpc_id}"
                
                try:
                    log_group_created = self._create_log_group_if_needed(log_group_name)
                    if not log_group_created:
                        results.append({
                            'item': f"VPC {vpc_id}",
                            'status': 'error',
                            'message': f"VPC '{vpc_id}'의 로그 그룹 생성에 실패했습니다."
                        })
                        continue

                    ec2.create_flow_logs(
                        ResourceIds=[vpc_id],
                        ResourceType='VPC',
                        TrafficType='ALL',
                        LogGroupName=log_group_name,
                        DeliverLogsPermissionArn=iam_role_arn
                    )
                    print(f"     [SUCCESS] VPC '{vpc_id}'에 Flow Log 생성 완료.\n")
                    results.append({
                        'item': f"VPC {vpc_id}",
                        'status': 'success',
                        'message': f"VPC '{vpc_id}'에 Flow Log를 생성했습니다."
                    })
                except ClientError as e:
                    print(f"     [ERROR] VPC '{vpc_id}'에 Flow Log 생성 실패: {e}\n")
                    results.append({
                        'item': f"VPC {vpc_id}",
                        'status': 'error',
                        'message': f"VPC '{vpc_id}'에 Flow Log 생성 실패: {str(e)}"
                    })

        # 다른 체커들과 일관된 형식으로 results 배열 직접 반환
        return results

    def _create_log_group_if_needed(self, log_group_name):
        """필요시 CloudWatch 로그 그룹 생성"""
        logs = self.session.client('logs')
        try:
            result = logs.describe_log_groups(logGroupNamePrefix=log_group_name)
            exists = any(g['logGroupName'] == log_group_name for g in result.get('logGroups', []))
            if not exists:
                print(f"     [INFO] 로그 그룹 '{log_group_name}'이 존재하지 않아 생성합니다.")
                logs.create_log_group(logGroupName=log_group_name)
                print(f"     [SUCCESS] 로그 그룹 생성 완료.")
            return log_group_name
        except ClientError as e:
            print(f"     [ERROR] 로그 그룹 생성 실패: {e}")
            return None

    def _get_or_create_common_iam_role(self):
        """공통 IAM 역할 생성 또는 기존 역할 사용"""
        iam = self.session.client('iam')
        role_name = "FlowLogsCommonRole"
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }

        try:
            iam.get_role(RoleName=role_name)
            print(f"  -> 공통 IAM 역할 '{role_name}'이 이미 존재합니다.")
        except ClientError:
            try:
                print(f"  -> IAM 역할 '{role_name}' 생성 중...")
                iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Common IAM role for VPC Flow Logs'  
                )
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforFlowLogs'
                )
                print(f"     [SUCCESS] IAM 역할 생성 및 정책 연결 완료.")
            except ClientError as e:
                print(f"     [ERROR] IAM 역할 생성 실패: {e}")
                return None

        return iam.get_role(RoleName=role_name)['Role']['Arn']

    def _get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('vpcs_without_logs'):
            return []
            
        vpcs_without_logs = diagnosis_result.get('vpcs_without_logs', [])
        
        return [{
            'id': 'enable_vpc_flow_logs',
            'title': 'VPC Flow Logs 활성화',
            'description': '선택한 VPC에서 Flow Logs를 활성화하고 CloudWatch 로그 그룹을 생성합니다.',
            'items': [
                {
                    'id': vpc_id,
                    'name': f"VPC {vpc_id}",
                    'description': "Flow Logs 미설정"
                }
                for vpc_id in vpcs_without_logs
            ]
        }]

    @property
    def item_code(self):
        return "4.11"
    
    @property
    def item_name(self):
        return "VPC 플로우 로깅 설정"