import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.4] 라우팅 테이블 정책 관리
    - 프라이빗 서브넷으로 추정되는(NAT GW로 라우팅되는) 라우팅 테이블에 IGW로 가는 경로가 있는지 점검
    """
    print("[INFO] 3.4 라우팅 테이블 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    misconfigured_rts = []

    try:
        response = ec2.describe_route_tables()
        for rt in response['RouteTables']:
            has_igw_route = False
            has_nat_route = False
            for route in rt.get('Routes', []):
                if route.get('GatewayId', '').startswith('igw-'):
                    has_igw_route = True
                if route.get('NatGatewayId', '').startswith('nat-'):
                    has_nat_route = True
            
            if has_igw_route and has_nat_route:
                rt_id = rt['RouteTableId']
                misconfigured_rts.append(f"라우팅 테이블 '{rt_id}'에 IGW와 NAT GW 경로가 모두 존재하여 구성 오류 가능성이 있습니다.")

        if not misconfigured_rts:
            print("[✓ COMPLIANT] 3.4 라우팅 테이블 구성에 명백한 오류가 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 3.4 잘못된 라우팅 정책이 의심되는 라우팅 테이블이 있습니다 ({len(misconfigured_rts)}건).")
            for finding in misconfigured_rts:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 프라이빗 서브넷은 NAT 게이트웨이를, 퍼블릭 서브넷은 인터넷 게이트웨이를 사용하도록 라우팅 경로를 명확히 분리하세요.")

    except ClientError as e:
        print(f"[ERROR] 라우팅 테이블 정보를 가져오는 중 오류 발생: {e}")
