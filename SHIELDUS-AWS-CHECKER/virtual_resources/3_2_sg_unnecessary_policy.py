import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리
    - 아웃바운드 규칙에서 모든 IP(0.0.0.0/0)로 모든 트래픽을 허용하는 경우를 점검.
    - 이는 기본 설정이지만, 데이터 유출 방지를 위해 검토가 필요함.
    """
    print("[INFO] 3.2 보안 그룹 아웃바운드 불필요 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    unrestricted_outbound_sgs = []

    try:
        response = ec2.describe_security_groups()
        for sg in response['SecurityGroups']:
            for rule in sg.get('IpPermissionsEgress', []):
                # 모든 프로토콜, 모든 포트, 모든 IP로의 아웃바운드
                if rule.get('IpProtocol') == '-1':
                    is_open_to_world = False
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            is_open_to_world = True
                            break
                    if not is_open_to_world:
                        for ipv6_range in rule.get('Ipv6Ranges', []):
                             if ipv6_range.get('CidrIpv6') == '::/0':
                                is_open_to_world = True
                                break
                    if is_open_to_world:
                        unrestricted_outbound_sgs.append(f"'{sg['GroupId']}' ({sg['GroupName']})")

        if not unrestricted_outbound_sgs:
            print("[✓ COMPLIANT] 3.2 모든 트래픽을 외부로 허용하는 아웃바운드 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.2 모든 트래픽을 외부로 허용하는 아웃바운드 규칙이 존재합니다 ({len(unrestricted_outbound_sgs)}개).")
            print(f"  ├─ 해당 SG: {', '.join(unrestricted_outbound_sgs)}")
            print("  └─ 🔧 이는 기본 설정일 수 있으나, 서버의 역할에 따라 필요한 최소한의 아웃바운드 트래픽만 허용하도록 규칙을 강화하세요.")
            
    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")