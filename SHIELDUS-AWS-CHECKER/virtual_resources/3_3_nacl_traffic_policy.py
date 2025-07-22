import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.3] 네트워크 ACL 인/아웃바운드 트래픽 정책 관리
    - 기본 네트워크 ACL이 아닌데 모든 트래픽을 허용하는 규칙이 있는지 점검
    """
    print("[INFO] 3.3 네트워크 ACL 트래픽 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_nacls = []

    try:
        response = ec2.describe_network_acls()
        for nacl in response['NetworkAcls']:
            # 기본 NACL은 점검에서 제외할 수 있으나, 가이드에 따라 일단 모두 점검
            is_default = nacl.get('IsDefault', False)
            nacl_id = nacl['NetworkAclId']
            
            for entry in nacl['Entries']:
                # 모든 트래픽 허용 규칙
                if entry.get('Protocol') == '-1' and entry.get('RuleAction') == 'allow':
                    direction = "인바운드" if not entry.get('Egress') else "아웃바운드"
                    source = entry.get('CidrBlock') or entry.get('Ipv6CidrBlock')
                    if source in ['0.0.0.0/0', '::/0']:
                        vulnerable_nacls.append(f"NACL '{nacl_id}' (Default: {is_default})에 모든 IP로부터의 모든 {direction} 트래픽 허용 규칙(#{entry['RuleNumber']})이 존재")

        if not vulnerable_nacls:
            print("[✓ COMPLIANT] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 존재합니다 ({len(vulnerable_nacls)}건).")
            for finding in vulnerable_nacls:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 NACL은 Stateless 방화벽이므로, 필요한 인/아웃바운드 트래픽을 명시적으로 허용하고 나머지는 거부하도록 정책을 강화하세요.")

    except ClientError as e:
        print(f"[ERROR] 네트워크 ACL 정보를 가져오는 중 오류 발생: {e}")