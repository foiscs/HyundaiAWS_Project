import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 3.virtual_resources/3_1_sg_any_rule.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리
    - 인바운드 규칙에서 모든 IP(0.0.0.0/0, ::/0)에 대해 주요 관리 포트(22, 3389)나 모든 포트가 열려 있는지 점검
    """
    print("[INFO] 3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_sgs = []
    critical_ports = {22: "SSH", 3389: "RDP"}

    try:
        response = ec2.describe_security_groups()
        for sg in response['SecurityGroups']:
            for rule in sg.get('IpPermissions', []):
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
                    from_port = rule.get('FromPort', -1)
                    to_port = rule.get('ToPort', -1)
                    
                    # 모든 포트가 열린 경우
                    if rule.get('IpProtocol') == '-1':
                        vulnerable_sgs.append(f"SG '{sg['GroupId']}' ({sg['GroupName']})에 모든 IP로부터 모든 트래픽(All traffic)이 허용됨")
                        continue

                    # 특정 포트/범위가 열린 경우
                    if from_port != -1:
                        # 주요 관리 포트 점검
                        for port, name in critical_ports.items():
                            if from_port <= port <= to_port:
                                vulnerable_sgs.append(f"SG '{sg['GroupId']}' ({sg['GroupName']})에 모든 IP로부터 위험한 포트 {port}({name})가 허용됨")

        if not vulnerable_sgs:
            print("[✓ COMPLIANT] 3.1 모든 IP에 개방된 위험한 인바운드 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.1 모든 IP에 개방된 위험한 인바운드 규칙이 존재합니다 ({len(vulnerable_sgs)}건).")
            for finding in vulnerable_sgs:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 소스 IP를 신뢰할 수 있는 특정 IP 대역으로 제한하거나 규칙을 삭제하세요.")
            print("  └─ 🔧 명령어: aws ec2 revoke-security-group-ingress --group-id <SG_ID> ...")

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")