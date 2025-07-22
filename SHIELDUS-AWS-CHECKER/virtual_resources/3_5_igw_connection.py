import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.5] 인터넷 게이트웨이 연결 관리
    - 어떤 VPC에도 연결되지 않은 'detached' 상태의 인터넷 게이트웨이가 있는지 점검
    """
    print("[INFO] 3.5 인터넷 게이트웨이 연결 관리 체크 중...")
    ec2 = boto3.client('ec2')
    detached_igws = []

    try:
        response = ec2.describe_internet_gateways()
        for igw in response['InternetGateways']:
            if not igw.get('Attachments'):
                detached_igws.append(igw['InternetGatewayId'])

        if not detached_igws:
            print("[✓ COMPLIANT] 3.5 모든 인터넷 게이트웨이가 VPC에 정상적으로 연결되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 3.5 VPC에 연결되지 않은 불필요한 인터넷 게이트웨이가 존재합니다 ({len(detached_igws)}개).")
            print(f"  ├─ 해당 IGW: {', '.join(detached_igws)}")
            print("  └─ 🔧 불필요한 리소스는 삭제하여 관리를 단순화하세요.")
            print("  └─ 🔧 명령어: aws ec2 delete-internet-gateway --internet-gateway-id <IGW_ID>")

    except ClientError as e:
        print(f"[ERROR] 인터넷 게이트웨이 정보를 가져오는 중 오류 발생: {e}")