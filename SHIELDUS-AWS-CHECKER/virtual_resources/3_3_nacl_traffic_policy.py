# 3.virtual_resources/3_3_nacl_traffic_policy.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.3] 네트워크 ACL 인/아웃바운드 트래픽 정책 관리
    - 모든 트래픽을 허용하는 규칙(#100번이 아닌 규칙)이 있는지 점검
    """
    print("[INFO] 3.3 네트워크 ACL 트래픽 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_nacls = []

    try:
        for nacl in ec2.describe_network_acls()['NetworkAcls']:
            for entry in nacl['Entries']:
                # 기본 규칙(100)과 마지막 거부 규칙(*)은 제외
                if entry['RuleNumber'] not in [100, 32767] and \
                   entry.get('Protocol') == '-1' and \
                   entry.get('RuleAction') == 'allow' and \
                   entry.get('CidrBlock') == '0.0.0.0/0':
                    direction = "인바운드" if not entry.get('Egress') else "아웃바운드"
                    vulnerable_nacls.append({
                        "NaclId": nacl['NetworkAclId'],
                        "RuleNumber": entry['RuleNumber'],
                        "Direction": direction,
                        "Egress": entry['Egress']
                    })
        
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