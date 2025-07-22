import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.6] NAT 게이트웨이 연결 관리
    - 생성되었지만 어떤 라우팅 테이블에서도 사용되지 않는 NAT 게이트웨이가 있는지 점검
    """
    print("[INFO] 3.6 NAT 게이트웨이 연결 관리 체크 중...")
    ec2 = boto3.client('ec2')
    unused_nat_gateways = []
    
    try:
        all_nat_ids = set()
        # 'available' 상태의 NAT GW만 점검
        nat_response = ec2.describe_nat_gateways(Filter=[{'Name': 'state', 'Values': ['available']}])
        for nat in nat_response['NatGateways']:
            all_nat_ids.add(nat['NatGatewayId'])

        used_nat_ids = set()
        rt_response = ec2.describe_route_tables()
        for rt in rt_response['RouteTables']:
            for route in rt['Routes']:
                if route.get('NatGatewayId'):
                    used_nat_ids.add(route['NatGatewayId'])
        
        unused_nat_ids = all_nat_ids - used_nat_ids

        if not unused_nat_ids:
            print("[✓ COMPLIANT] 3.6 모든 NAT 게이트웨이가 라우팅 테이블에서 사용 중입니다.")
        else:
            print(f"[⚠ WARNING] 3.6 라우팅 테이블에서 사용되지 않는 NAT 게이트웨이가 존재합니다 ({len(unused_nat_ids)}개).")
            print(f"  ├─ 해당 NAT GW: {', '.join(unused_nat_ids)}")
            print("  └─ 🔧 불필요한 NAT 게이트웨이는 비용을 발생시키므로 삭제하세요.")
            print("  └─ 🔧 명령어: aws ec2 delete-nat-gateway --nat-gateway-id <NAT_GW_ID>")

    except ClientError as e:
        print(f"[ERROR] NAT 게이트웨이 또는 라우팅 테이블 정보를 가져오는 중 오류 발생: {e}")