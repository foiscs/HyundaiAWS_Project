import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리
    - 인바운드 및 아웃바운드 규칙에서 모든 IP(0.0.0.0/0, ::/0)에 대해 모든 포트가 열려 있는지 점검
    """
    print("[INFO] 3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_rules = []

    try:
        for sg in ec2.describe_security_groups()['SecurityGroups']:
            # Ingress (Inbound)
            for rule in sg.get('IpPermissions', []):
                vulnerable_rules.extend(_check_rule(sg, rule, direction='ingress'))
            # Egress (Outbound)
            for rule in sg.get('IpPermissionsEgress', []):
                vulnerable_rules.extend(_check_rule(sg, rule, direction='egress'))

        if not vulnerable_rules:
            print("[✓ COMPLIANT] 3.1 ANY 포트가 열려 있는 인/아웃바운드 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.1 ANY 포트가 열려 있는 규칙이 존재합니다 ({len(vulnerable_rules)}건).")
            for finding in vulnerable_rules:
                print(f"  ├─ [{finding['Direction'].upper()}] SG '{finding['GroupId']}' ({finding['GroupName']}): 소스 {finding['Source']}에 전체 포트 허용")

        return vulnerable_rules

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def _check_rule(sg, rule, direction='ingress'):
    findings = []
    if rule.get('IpProtocol') == '-1' or (
        rule.get('FromPort') == 0 and rule.get('ToPort') == 65535
    ):
        for ip_range in rule.get('IpRanges', []):
            if ip_range.get('CidrIp') == '0.0.0.0/0':
                findings.append({
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Source': '0.0.0.0/0',
                    'Rule': rule,
                    'Direction': direction
                })
        for ipv6_range in rule.get('Ipv6Ranges', []):
            if ipv6_range.get('CidrIpv6') == '::/0':
                findings.append({
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Source': '::/0',
                    'Rule': rule,
                    'Direction': direction
                })
    return findings

def fix(vulnerable_rules_details):
    """
    [3.1] 보안 그룹 ANY 설정 관리 조치
    - 사용자 확인 후 위험한 인바운드/아웃바운드 규칙을 제거
    """
    if not vulnerable_rules_details:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.1 보안 그룹 ANY 포트 규칙에 대한 조치를 시작합니다.")
    for detail in vulnerable_rules_details:
        direction = "ingress" if detail['Rule']['IpProtocol'] != '-1' else "egress"
        choice = input(
            f"  -> SG '{detail['GroupId']}' {direction} 규칙에서 '{detail['Source']}' -> 전체 포트를 제거하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            try:
                ip_permission = {
                    'IpProtocol': detail['Rule']['IpProtocol'],
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}] if '0.0.0.0/0' in detail['Source'] else [],
                    'Ipv6Ranges': [{'CidrIpv6': '::/0'}] if '::/0' in detail['Source'] else []
                }

                if detail['Rule']['IpProtocol'] != '-1':
                    ip_permission['FromPort'] = detail['Rule'].get('FromPort')
                    ip_permission['ToPort'] = detail['Rule'].get('ToPort')

                revoke_func = ec2.revoke_security_group_ingress if direction == 'ingress' else ec2.revoke_security_group_egress
                revoke_func(GroupId=detail['GroupId'], IpPermissions=[ip_permission])
                print(f"     [SUCCESS] SG '{detail['GroupId']}'에서 해당 규칙을 제거했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 규칙 제거 실패: {e}")
        else:
            print(f"     [INFO] SG '{detail['GroupId']}'의 규칙 제거를 건너뜁니다.")

if __name__ == "__main__":
    rules = check()
    fix(rules)
