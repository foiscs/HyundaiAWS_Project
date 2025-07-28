"""
[4.12] 로그 보존 기간 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_12_log_retention_period.py
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class LogRetentionPeriodChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.12"
    
    @property 
    def item_name(self):
        return "로그 보존 기간 설정"
        
    def run_diagnosis(self):
        """
        [4.12] VPC 플로우 로깅 설정 체크
        """
        print("[INFO] 4.11 VPC 플로우 로깅 설정 체크 중...")
        ec2 = boto3.client('ec2')

        try:
            all_vpcs = {vpc['VpcId'] for vpc in ec2.describe_vpcs()['Vpcs']}
            active_logs = {f['ResourceId'] for f in ec2.describe_flow_logs()['FlowLogs'] if f['FlowLogStatus'] == 'ACTIVE'}
            vpcs_without_logs = list(all_vpcs - active_logs)

            if not vpcs_without_logs:
                print("[✓ COMPLIANT] 4.11 모든 VPC에 Flow Logs가 활성화되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 4.11 Flow Logs가 비활성화된 VPC가 존재합니다 ({len(vpcs_without_logs)}개).")
                print(f"  ├─ 해당 VPC: {', '.join(vpcs_without_logs)}")

            has_issues = len(vpcs_without_logs) > 0
            total_issues = len(vpcs_without_logs)
            risk_level = self.calculate_risk_level(total_issues)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"Flow Logs가 비활성화된 VPC {total_issues}개 발견" if has_issues else "모든 VPC에 Flow Logs가 활성화되어 있습니다",
                'findings': vpcs_without_logs,
                'summary': f"Flow Logs 비활성화 VPC {len(vpcs_without_logs)}개" if has_issues else "모든 VPC Flow Logs가 정상적으로 활성화되어 있습니다.",
                'details': {
                    'total_vpcs': len(all_vpcs),
                    'vpcs_with_logs': len(all_vpcs) - len(vpcs_without_logs),
                    'vpcs_without_logs': len(vpcs_without_logs),
                    'vpcs_without_logs_list': vpcs_without_logs
                }
            }

        except ClientError as e:
            print(f"[ERROR] VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def create_iam_role_with_timestamp(self):
        """타임스탬프가 포함된 IAM 역할 생성"""
        iam = boto3.client('iam')
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        role_name = f"FlowLogsRole-{timestamp}"
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        try:
            print(f"  -> IAM 역할 '{role_name}'을 생성 중...")
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='VPC Flow Logs IAM Role'
            )
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonVPCFlowLogs'
            )
            print(f"     [SUCCESS] IAM 역할 생성 및 정책 연결 완료: {role_name}")
            return iam.get_role(RoleName=role_name)['Role']['Arn']
        except ClientError as e:
            print(f"     [ERROR] IAM 역할 생성 실패: {e}")
            return None

    def execute_fix(self, selected_items):
        """
        [4.12] VPC Flow Logs 생성 조치
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': 'VPC Flow Logs 조치가 필요한 항목이 없습니다.'}

        vpcs_without_logs = diagnosis_result['findings']

        print("[FIX] 4.11 VPC Flow Logs 생성 조치를 시작합니다.")
        print("→ 이 작업은 CloudWatch 로그 그룹과 IAM 역할을 자동으로 생성하고,")
        print("   각 VPC에 대해 Flow Logs 설정을 순차적으로 진행합니다.")
        print("→ 먼저 공통 로그 그룹과 IAM 역할을 준비합니다.\n")

        ec2 = boto3.client('ec2')
        logs = boto3.client('logs')

        default_log_group = "/vpc/flowlogs"

        try:
            result = logs.describe_log_groups(logGroupNamePrefix=default_log_group)
            exists = any(g['logGroupName'] == default_log_group for g in result.get('logGroups', []))
            if not exists:
                print(f"  -> 로그 그룹 '{default_log_group}' 생성 중...")
                logs.create_log_group(logGroupName=default_log_group)
                print(f"     [SUCCESS] 로그 그룹 생성 완료.")
            else:
                print(f"  -> 로그 그룹 '{default_log_group}'은 이미 존재합니다.")
        except ClientError as e:
            print(f"     [ERROR] 로그 그룹 처리 실패: {e}")
            return {
                'status': 'error',
                'message': f"로그 그룹 처리 실패: {str(e)}"
            }

        log_group_name = default_log_group
        iam_role_arn = self.create_iam_role_with_timestamp()
        if not iam_role_arn:
            print("     [ERROR] IAM 역할이 없으므로 조치를 중단합니다.")
            return {
                'status': 'error',
                'message': 'IAM 역할 생성 실패로 조치를 중단합니다.'
            }

        print("\n→ 이제 각 VPC에 대해 Flow Logs 설정을 진행합니다.\n")
        results = []
        
        for vpc_id in vpcs_without_logs:
            # 선택된 항목인지 확인
            if any(vpc_id in str(item) for item in selected_items.values() for item in item):
                try:
                    ec2.create_flow_logs(
                        ResourceIds=[vpc_id],
                        ResourceType='VPC',
                        TrafficType='ALL',
                        LogGroupName=log_group_name,
                        DeliverLogsPermissionArn=iam_role_arn
                    )
                    print(f"     [SUCCESS] VPC '{vpc_id}'에 Flow Log 생성 완료.")
                    results.append({
                        'status': 'success',
                        'resource': vpc_id,
                        'action': 'VPC Flow Log 생성',
                        'message': f"VPC '{vpc_id}'에 Flow Log를 생성했습니다."
                    })
                except ClientError as e:
                    print(f"     [ERROR] Flow Log 생성 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': vpc_id,
                        'error': str(e),
                        'message': f"VPC '{vpc_id}' Flow Log 생성 실패: {str(e)}"
                    })
            else:
                print(f"     [SKIP] VPC '{vpc_id}'는 건너뜁니다.")

        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return {
            'status': 'success' if success_count > 0 else 'partial_success',
            'results': results,
            'message': f"{success_count}개 VPC에 대한 Flow Log 생성이 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('findings'):
            return []
            
        vpcs_without_logs = diagnosis_result.get('findings', [])
        options = []
        
        # Flow Logs가 비활성화된 VPC
        if vpcs_without_logs:
            options.append({
                'id': 'create_vpc_flow_logs',
                'title': 'VPC Flow Logs 생성',
                'description': '선택한 VPC에 Flow Logs를 생성합니다.',
                'items': [
                    {
                        'id': vpc_id,
                        'name': f"VPC {vpc_id}",
                        'description': "Flow Logs 비활성화됨"
                    }
                    for vpc_id in vpcs_without_logs
                ]
            })
        
        return options

    @property
    def item_code(self):
        return "4.12"
    
    @property 
    def item_name(self):
        return "로그 보존 기간 설정"