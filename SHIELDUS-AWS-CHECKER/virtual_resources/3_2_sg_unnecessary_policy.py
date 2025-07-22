# 3.virtual_resources/3_2_sg_unnecessary_policy.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리
    - 아웃바운드 규칙에서 모든 IP(0.0.0.0/0)로 모든 트래픽을 허용하는 경우를 점검
    """
    print("[INFO] 3.2 보안 그룹 아웃바운드 불필요 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    unrestricted_sgs = []

    try:
        for sg in ec2.describe_security_groups()['SecurityGroups']:
            for rule in sg.get('IpPermissionsEgress', []):
                if rule.get('IpProtocol') == '-1':
                    if any(r.get('CidrIp') == '0.0.0.0/0' for r in rule.get('IpRanges', [])) or \
                       any(r.get('CidrIpv6') == '::/0' for r in rule.get('Ipv6Ranges', [])):
                        unrestricted_sgs.append(sg['GroupId'])
                        break
        
        if not unrestricted_sgs:
            print("[✓ COMPLIANT] 3.2 모든 트래픽을 외부로 허용하는 아웃바운드 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.2 모든 트래픽을 외부로 허용하는 아웃바운드 규칙이 존재합니다 ({len(unrestricted_sgs)}개).")
            print(f"  ├─ 해당 SG: {', '.join(unrestricted_sgs)}")
            print("  └─ 이는 기본 설정일 수 있으나, 서버 역할에 따라 최소한의 아웃바운드 규칙만 허용하도록 강화를 권장합니다.")
            
        return unrestricted_sgs

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(unrestricted_sgs):
    """
    [3.2] 보안 그룹 아웃바운드 불필요 정책 관리 조치
    - 기본 아웃바운드 규칙 제거는 매우 위험하므로 자동화하지 않고 수동 조치 가이드만 제공
    """
    if not unrestricted_sgs:
        return

    print("[FIX] 3.2 '아웃바운드 모든 트래픽 허용' 규칙의 자동 조치는 서비스 중단을 유발할 수 있어 지원하지 않습니다.")
    print("  └─ 애플리케이션이 외부와 통신해야 하는 필수 포트(예: 80, 443)와 대상 IP를 먼저 파악해야 합니다.")
    print("  └─ 1. 필요한 아웃바운드 규칙(예: HTTPS to 0.0.0.0/0)을 먼저 추가합니다.")
    print("  └─ 2. 충분한 테스트 후, 아래 명령어를 사용하여 기존의 '모든 트래픽' 허용 규칙을 수동으로 제거하세요.")
    for sg_id in unrestricted_sgs:
        print(f"     aws ec2 revoke-security-group-egress --group-id {sg_id} --protocol -1 --port -1 --cidr 0.0.0.0/0")

if __name__ == "__main__":
    sg_list = check()
    fix(sg_list)