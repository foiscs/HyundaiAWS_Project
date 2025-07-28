#  4.operation/4_11_vpc_flow_logging.py
import boto3
import json
import time
from botocore.exceptions import ClientError

def check():
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

        return vpcs_without_logs

    except ClientError as e:
        print(f"[ERROR] VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {e}")
        return []

def create_log_group_if_needed(log_group_name):
    logs = boto3.client('logs')
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

def get_or_create_common_iam_role():
    iam = boto3.client('iam')
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

def fix(vpcs_without_logs):
    if not vpcs_without_logs:
        return

    print("[FIX] 4.11 VPC Flow Logs 설정 조치를 시작합니다.")
    print("→ 각 VPC에 대해 별도 로그 그룹을 생성하고, 공통 IAM 역할을 사용합니다.\n")

    ec2 = boto3.client('ec2')
    iam_role_arn = get_or_create_common_iam_role()
    if not iam_role_arn:
        print("     [ERROR] IAM 역할 생성 실패로 인해 조치를 중단합니다.")
        return

    for vpc_id in vpcs_without_logs:
        log_group_name = f"/vpc/flowlogs/{vpc_id}"
        response = input(f"  → VPC '{vpc_id}'에 대해 Flow Logs를 생성하고 로그 그룹 '{log_group_name}'을 만들까요? (y/n): ").lower()
        if response != 'y':
            print(f"     [SKIP] VPC '{vpc_id}'는 건너뜁니다.\n")
            continue

        log_group_created = create_log_group_if_needed(log_group_name)
        if not log_group_created:
            continue

        try:
            ec2.create_flow_logs(
                ResourceIds=[vpc_id],
                ResourceType='VPC',
                TrafficType='ALL',
                LogGroupName=log_group_name,
                DeliverLogsPermissionArn=iam_role_arn
            )
            print(f"     [SUCCESS] VPC '{vpc_id}'에 Flow Log 생성 완료.\n")
        except ClientError as e:
            print(f"     [ERROR] VPC '{vpc_id}'에 Flow Log 생성 실패: {e}\n")

if __name__ == "__main__":
    vpcs = check()
    fix(vpcs)
