import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 3.virtual_resources/3_8_rds_subnet_az.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.8] RDS 서브넷 가용 영역 관리
    - RDS DB 서브넷 그룹이 2개 미만의 가용 영역(AZ)을 사용하여 구성되었는지 점검
    """
    print("[INFO] 3.8 RDS 서브넷 가용 영역 관리 체크 중...")
    rds = boto3.client('rds')
    single_az_subnet_groups = []

    try:
        response = rds.describe_db_subnet_groups()
        for group in response['DBSubnetGroups']:
            az_set = set()
            for subnet in group['Subnets']:
                az_set.add(subnet['SubnetAvailabilityZone']['Name'])
            
            if len(az_set) < 2:
                single_az_subnet_groups.append(group['DBSubnetGroupName'])

        if not single_az_subnet_groups:
            print("[✓ COMPLIANT] 3.8 모든 RDS DB 서브넷 그룹이 Multi-AZ로 구성되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 3.8 Single-AZ로 구성된 DB 서브넷 그룹이 존재합니다 ({len(single_az_subnet_groups)}개).")
            print(f"  ├─ 해당 서브넷 그룹: {', '.join(single_az_subnet_groups)}")
            print("  └─ 🔧 고가용성을 위해 최소 2개 이상의 다른 가용 영역에 속한 서브넷을 추가하세요.")

    except ClientError as e:
        print(f"[ERROR] RDS DB 서브넷 그룹 정보를 가져오는 중 오류 발생: {e}")