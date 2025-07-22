import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_11_vpc_flow_logging.py
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
        vpcs = ec2.describe_vpcs().get('Vpcs', [])
        all_vpc_ids = {vpc['VpcId'] for vpc in vpcs}
        
        flow_logs = ec2.describe_flow_logs().get('FlowLogs', [])
        vpcs_with_flow_logs = {fl['ResourceId'] for fl in flow_logs if fl['FlowLogStatus'] == 'ACTIVE' and fl['ResourceId'] in all_vpc_ids}
        
        vpcs_without_flow_logs = list(all_vpc_ids - vpcs_with_flow_logs)

        if not vpcs_without_flow_logs:
            print("[✓ COMPLIANT] 4.11 모든 VPC에 Flow Logs가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.11 Flow Logs가 비활성화된 VPC가 존재합니다 ({len(vpcs_without_flow_logs)}개).")
            print(f"  ├─ 해당 VPC: {', '.join(vpcs_without_flow_logs)}")
            print("  └─ 🔧 VPC 대시보드에서 해당 VPC를 선택하고 [작업] > [플로우 로그 생성]을 통해 설정을 활성화하세요.")
    
    except ClientError as e:
        print(f"[ERROR] VPC 또는 Flow Logs 정보를 가져오는 중 오류 발생: {e}")