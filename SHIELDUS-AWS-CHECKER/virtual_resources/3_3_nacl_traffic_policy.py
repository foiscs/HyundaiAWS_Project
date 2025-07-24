import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.3] 네트워크 ACL 인/아웃바운드 트래픽 정책 관리
    - 모든 트래픽을 허용하는 광범위 규칙이 있는지 점검 (프로토콜 -1, 포트 전체, CIDR 0.0.0.0/0, Allow)
    """
    print("[INFO] 3.3 네트워크 ACL 트래픽 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_nacls = []

    try:
        # 1. 모든 네트워크 ACL 조회
        nacls = ec2.describe_network_acls()['NetworkAcls']
        for nacl in nacls:
            for entry in nacl['Entries']:
                # 2. 규칙 필드 수집
                rule_num = entry.get('RuleNumber')
                protocol = entry.get('Protocol')
                rule_action = entry.get('RuleAction')
                cidr = entry.get('CidrBlock', '')
                egress = entry.get('Egress', False)
                port_range = entry.get('PortRange', {})

                # 3. 점검 조건
                is_all_protocol = protocol == '-1'
                is_all_port = port_range == {}  # 포트 범위 전체 허용 (없으면 전체 허용)
                is_all_cidr = cidr == '0.0.0.0/0'
                is_allow = rule_action == 'allow'

                if is_all_protocol and is_all_port and is_all_cidr and is_allow:
                    direction = "아웃바운드" if egress else "인바운드"
                    vulnerable_nacls.append({
                        "NaclId": nacl['NetworkAclId'],
                        "RuleNumber": rule_num,
                        "Direction": direction,
                        "Egress": egress
                    })

        # 4. 결과 출력
        if not vulnerable_nacls:
            print("[✓ COMPLIANT] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.3 모든 트래픽을 허용하는 광범위한 NACL 규칙이 존재합니다 ({len(vulnerable_nacls)}건).")
            for f in vulnerable_nacls:
                print(f"  ├─ NACL '{f['NaclId']}'에 모든 {f['Direction']} 트래픽 허용 규칙(#{f['RuleNumber']})이 존재")

        return vulnerable_nacls

    except ClientError as e:
        print(f"[ERROR] 네트워크 ACL 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(vulnerable_nacls):
    """
    [3.3] 네트워크 ACL 트래픽 정책 관리 조치
    - 사용자 확인 후 광범위한 허용 규칙을 삭제
    """
    if not vulnerable_nacls:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.3 광범위한 NACL 규칙에 대한 조치를 시작합니다.")
    for nacl_info in vulnerable_nacls:
        choice = input(f"  -> NACL '{nacl_info['NaclId']}'의 규칙 #{nacl_info['RuleNumber']} ({nacl_info['Direction']})을(를) 삭제하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            try:
                ec2.delete_network_acl_entry(
                    NetworkAclId=nacl_info['NaclId'],
                    RuleNumber=nacl_info['RuleNumber'],
                    Egress=nacl_info['Egress']
                )
                print(f"     [SUCCESS] 규칙 #{nacl_info['RuleNumber']}을(를) 삭제했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 규칙 삭제 실패: {e}")
        else:
            print(f"     [INFO] NACL '{nacl_info['NaclId']}'의 규칙 삭제를 건너뜁니다.")

if __name__ == "__main__":
    nacl_list = check()
    fix(nacl_list)
