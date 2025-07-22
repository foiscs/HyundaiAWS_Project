import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.1] 보안 그룹 인/아웃바운드 ANY 설정 관리
    - 인바운드 규칙에서 모든 IP(0.0.0.0/0, ::/0)에 대해 주요 관리 포트(22, 3389)나 모든 포트가 열려 있는지 점검
    """
    print("[INFO] 3.1 보안 그룹 인/아웃바운드 ANY 설정 관리 체크 중...")
    ec2 = boto3.client('ec2')
    vulnerable_rules_details = []
    critical_ports = {22: "SSH", 3389: "RDP"}

    try:
        for sg in ec2.describe_security_groups()['SecurityGroups']:
            for rule in sg.get('IpPermissions', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        vulnerable_rules_details.extend(
                            _analyze_rule(sg, rule, ip_range.get('CidrIp'), critical_ports)
                        )
                for ipv6_range in rule.get('Ipv6Ranges', []):
                    if ipv6_range.get('CidrIpv6') == '::/0':
                         vulnerable_rules_details.extend(
                            _analyze_rule(sg, rule, ipv6_range.get('CidrIpv6'), critical_ports)
                        )

        if not vulnerable_rules_details:
            print("[✓ COMPLIANT] 3.1 모든 IP에 개방된 위험한 인바운드 규칙이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.1 모든 IP에 개방된 위험한 인바운드 규칙이 존재합니다 ({len(vulnerable_rules_details)}건).")
            for finding in vulnerable_rules_details:
                print(f"  ├─ SG '{finding['GroupId']}' ({finding['GroupName']}): 포트 {finding['Port']}에 대해 소스 '{finding['Source']}' 허용")
        
        return vulnerable_rules_details

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def _analyze_rule(sg, rule, source, critical_ports):
    findings = []
    from_port = rule.get('FromPort', -1)
    to_port = rule.get('ToPort', -1)
    
    # 모든 포트
    if rule.get('IpProtocol') == '-1':
        findings.append({
            "GroupId": sg['GroupId'], "GroupName": sg['GroupName'], "Port": "All", "Source": source, "Rule": rule
        })
    # 주요 관리 포트
    elif from_port != -1:
        for port, name in critical_ports.items():
            if from_port <= port <= to_port:
                findings.append({
                    "GroupId": sg['GroupId'], "GroupName": sg['GroupName'], "Port": f"{port}({name})", "Source": source, "Rule": rule
                })
    return findings

def fix(vulnerable_rules_details):
    """
    [3.1] 보안 그룹 ANY 설정 관리 조치
    - 사용자 확인 후 위험한 인바운드 규칙을 제거
    """
    if not vulnerable_rules_details:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.1 위험한 보안 그룹 규칙에 대한 조치를 시작합니다.")
    for detail in vulnerable_rules_details:
        choice = input(f"  -> SG '{detail['GroupId']}'의 '{detail['Source']}' -> Port {detail['Port']} 규칙을 제거하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            try:
                ip_permissions_to_revoke = [{
                    'IpProtocol': detail['Rule']['IpProtocol'],
                    'FromPort': detail['Rule'].get('FromPort'),
                    'ToPort': detail['Rule'].get('ToPort'),
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}] if '0.0.0.0/0' in detail['Source'] else [],
                    'Ipv6Ranges': [{'CidrIpv6': '::/0'}] if '::/0' in detail['Source'] else []
                }]
                ec2.revoke_security_group_ingress(GroupId=detail['GroupId'], IpPermissions=ip_permissions_to_revoke)
                print(f"     [SUCCESS] SG '{detail['GroupId']}'에서 해당 규칙을 제거했습니다.")
            except ClientError as e:
                print(f"     [ERROR] 규칙 제거 실패: {e}")
        else:
            print(f"     [INFO] SG '{detail['GroupId']}'의 규칙 제거를 건너뜁니다.")

if __name__ == "__main__":
    rules = check()
    fix(rules)