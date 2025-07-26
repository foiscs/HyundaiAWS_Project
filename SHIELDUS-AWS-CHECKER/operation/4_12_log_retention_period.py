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

def create_iam_role_with_timestamp():
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

def fix(vpcs_without_logs):
    if not vpcs_without_logs:
        return

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
        return

    log_group_name = default_log_group
    iam_role_arn = create_iam_role_with_timestamp()
    if not iam_role_arn:
        print("     [ERROR] IAM 역할이 없으므로 조치를 중단합니다.")
        return

    print("\n→ 이제 각 VPC에 대해 Flow Logs 설정 여부를 개별적으로 확인합니다.\n")
    for vpc_id in vpcs_without_logs:
        if input(f"  → VPC '{vpc_id}'에 Flow Log를 생성하시겠습니까? (y/n): ").lower() == 'y':
            try:
                ec2.create_flow_logs(
                    ResourceIds=[vpc_id],
                    ResourceType='VPC',
                    TrafficType='ALL',
                    LogGroupName=log_group_name,
                    DeliverLogsPermissionArn=iam_role_arn
                )
                print(f"     [SUCCESS] VPC '{vpc_id}'에 Flow Log 생성 완료.")
            except ClientError as e:
                print(f"     [ERROR] Flow Log 생성 실패: {e}")
        else:
            print(f"     [SKIP] VPC '{vpc_id}'는 건너뜁니다.")

if __name__ == "__main__":
    vpcs = check()
    fix(vpcs)
