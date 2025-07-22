import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.11] VPC 플로우 로깅 설정
    - 모든 VPC에 대해 Flow Logs가 활성화되어 있는지 점검
    """
    print("[INFO] 4.11 VPC 플로우 로깅 설정 체크 중...")
    ec2 = boto3.client('ec2')
    
    try:
        all_vpcs = {vpc['VpcId'] for vpc in ec2.describe_vpcs()['Vpcs']}
        vpcs_with_logs = {fl['ResourceId'] for fl in ec2.describe_flow_logs()['FlowLogs'] if fl['FlowLogStatus'] == 'ACTIVE'}
        vpcs_without_logs = list(all_vpcs - vpcs_with_logs)

        if not vpcs_without_logs:
            print("[✓ COMPLIANT] 4.11 모든 VPC에 Flow Logs가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.11 Flow Logs가 비활성화된 VPC가 존재합니다 ({len(vpcs_without_logs)}개).")
            print(f"  ├─ 해당 VPC: {', '.join(vpcs_without_logs)}")
        
        return vpcs_without_logs
    
    except ClientError as e:
        print(f"[ERROR] VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(vpcs_without_logs):
    """
    [4.11] VPC 플로우 로깅 설정 조치
    - Flow Logs가 없는 VPC에 대해 Flow Log 생성
    """
    if not vpcs_without_logs: return

    ec2 = boto3.client('ec2')
    iam = boto3.client('iam')
    logs = boto3.client('logs')
    print("[FIX] 4.11 VPC Flow Logs 생성 조치를 시작합니다.")
    
    log_group_name = input("  -> Flow Logs를 저장할 CloudWatch 로그 그룹 이름을 입력하세요: ").strip()
    iam_role_arn = input("  -> Flow Logs에 필요한 IAM 역할 ARN을 입력하세요: ").strip()
    
    if not log_group_name or not iam_role_arn:
        print("     [ERROR] 로그 그룹과 IAM 역할 ARN은 필수입니다. 조치를 중단합니다.")
        return

    try: # 로그 그룹 존재 확인
        logs.describe_log_groups(logGroupNamePrefix=log_group_name)
    except ClientError:
        print(f"     [ERROR] 로그 그룹 '{log_group_name}'을(를) 찾을 수 없습니다.")
        return
    try: # IAM 역할 존재 확인
        iam.get_role(RoleName=iam_role_arn.split('/')[-1])
    except ClientError:
        print(f"     [ERROR] IAM 역할 '{iam_role_arn}'을(를) 찾을 수 없습니다.")
        return

    for vpc_id in vpcs_without_logs:
        if input(f"  -> VPC '{vpc_id}'에 Flow Log를 생성하시겠습니까? (y/n): ").lower() == 'y':
            try:
                ec2.create_flow_logs(
                    ResourceIds=[vpc_id],
                    ResourceType='VPC',
                    TrafficType='ALL',
                    LogGroupName=log_group_name,
                    DeliverLogsPermissionArn=iam_role_arn
                )
                print(f"     [SUCCESS] VPC '{vpc_id}'에 Flow Log를 생성했습니다.")
            except ClientError as e:
                print(f"     [ERROR] Flow Log 생성 실패: {e}")

if __name__ == "__main__":
    vpcs = check()
    fix(vpcs)