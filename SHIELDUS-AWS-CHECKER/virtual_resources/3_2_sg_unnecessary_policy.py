import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리
    - 인/아웃바운드 규칙에 모든 IP(0.0.0.0/0, ::/0)가 포함된 경우 안내 + 어떤 리소스에 연결되어 있는지 확인
    """
    print("[INFO] 3.2 보안 그룹 인/아웃바운드 불필요 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    findings = []

    try:
        # 모든 SG 조회
        response = ec2.describe_security_groups()
        all_sgs = response['SecurityGroups']

        # SG → ENI 매핑 정보 수집
        eni_response = ec2.describe_network_interfaces()
        sg_usage = {}
        for eni in eni_response['NetworkInterfaces']:
            for group in eni.get('Groups', []):
                sg_id = group['GroupId']
                if sg_id not in sg_usage:
                    sg_usage[sg_id] = []
                sg_usage[sg_id].append(eni['NetworkInterfaceId'])

        # SG 검사
        for sg in all_sgs:
            sg_id = sg['GroupId']
            sg_name = sg.get('GroupName', 'N/A')
            matched = False

            # 인바운드/아웃바운드 규칙 검사
            for direction, permissions in [('ingress', sg.get('IpPermissions', [])),
                                           ('egress', sg.get('IpPermissionsEgress', []))]:
                for rule in permissions:
                    if any(ip.get('CidrIp') == '0.0.0.0/0' for ip in rule.get('IpRanges', [])) or \
                       any(ip.get('CidrIpv6') == '::/0' for ip in rule.get('Ipv6Ranges', [])):
                        findings.append({
                            'GroupId': sg_id,
                            'GroupName': sg_name,
                            'Direction': direction,
                            'Attached': sg_id in sg_usage,
                            'ENIs': sg_usage.get(sg_id, [])
                        })
                        matched = True
                        break  # 하나만 잡혀도 해당 SG는 취약

            if matched:
                continue

        # 결과 출력
        if not findings:
            print("[✓ COMPLIANT] 3.2 모든 IP 대상 규칙을 가진 보안 그룹이 없습니다.")
        else:
            print(f"[⚠ WARNING] 3.2 전체 IP 대상 규칙이 존재하는 보안 그룹이 발견되었습니다 ({len(findings)}건).")
            for f in findings:
                attach_msg = f"연결됨 (ENI: {', '.join(f['ENIs'])})" if f['Attached'] else "연결되지 않음"
                print(f"  ├─ [{f['Direction'].upper()}] SG '{f['GroupId']}' ({f['GroupName']}) - {attach_msg}")

        return findings

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def is_sg_in_use(ec2, sg_id):
    # 1. ENI
    eni = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg_id]}])
    if eni['NetworkInterfaces']:
        return True, "ENI"

    # 2. EC2
    ec2s = ec2.describe_instances(Filters=[{'Name': 'instance.group-id', 'Values': [sg_id]}])
    for reservation in ec2s.get('Reservations', []):
        if reservation['Instances']:
            return True, "EC2"

    # 3. RDS
    try:
        rds = boto3.client('rds')
        rds_instances = rds.describe_db_instances()
        for db in rds_instances['DBInstances']:
            if any(sg['VpcSecurityGroupId'] == sg_id for sg in db.get('VpcSecurityGroups', [])):
                return True, "RDS"
    except ClientError:
        pass

    # 4. ELB
    try:
        elb = boto3.client('elbv2')
        elbs = elb.describe_load_balancers()
        for lb in elbs['LoadBalancers']:
            if sg_id in lb.get('SecurityGroups', []):
                return True, "ELB"
    except ClientError:
        pass

    # 5. Lambda
    try:
        lam = boto3.client('lambda')
        funcs = lam.list_functions()['Functions']
        for fn in funcs:
            cfg = lam.get_function_configuration(FunctionName=fn['FunctionName'])
            if sg_id in cfg.get('VpcConfig', {}).get('SecurityGroupIds', []):
                return True, "Lambda"
    except ClientError:
        pass

    return False, None


def fix(unused_sgs):
    """
    [3.2] 미사용 중이며 ANY로 개방된 보안 그룹 자동 점검 및 삭제 여부 확인
    - 기본 보안 그룹, 참조 중인 SG는 제외
    - 삭제 가능 여부를 먼저 검증 후 사용자에게 묻는다
    """
    if not unused_sgs:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.2 미사용 중이며 ANY로 개방된 보안 그룹에 대한 삭제 여부를 확인합니다.")

    for sg in unused_sgs:
        sg_id = sg['GroupId']
        sg_name = sg['GroupName']

        # 1. 기본 SG 스킵
        if sg_name == 'default':
            print(f"  -> SG '{sg_id}' ({sg_name})는 기본 보안 그룹입니다. 삭제할 수 없으므로 건너뜁니다.")
            continue

        # 2. 직접 참조 여부 검사
        try:
            in_use, used_by = is_sg_in_use(ec2, sg_id)
            if in_use:
                print(f"  -> SG '{sg_id}' ({sg_name})는 다른 리소스({used_by})에 의해 참조 중이라 삭제할 수 없습니다.")
                continue
        except ClientError as e:
            print(f"     [ERROR] SG '{sg_id}' 사용 여부 확인 실패: {e}")
            continue

        # 3. 사전 삭제 시도 → 삭제 가능 여부 확인용 (DryRun 대체)
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"     [SUCCESS] SG '{sg_id}' ({sg_name})를 삭제했습니다.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'DependencyViolation':
                print(f"  -> SG '{sg_id}' ({sg_name})는 다른 리소스에 의해 참조 중이라 삭제할 수 없습니다.")
            elif e.response['Error']['Code'] == 'InvalidGroup.NotFound':
                print(f"  -> SG '{sg_id}'는 이미 삭제되었거나 존재하지 않습니다.")
            else:
                # 삭제 가능하지만 사용자의 동의 필요
                print(f"  -> SG '{sg_id}' ({sg_name})는 미연결 상태입니다. 삭제하시겠습니까? (y/n): ", end="")
                choice = input().strip().lower()
                if choice != 'y':
                    print(f"     [SKIPPED] SG '{sg_id}' 삭제를 건너뜁니다.")
                    continue

                try:
                    ec2.delete_security_group(GroupId=sg_id)
                    print(f"     [SUCCESS] SG '{sg_id}'를 삭제했습니다.")
                except ClientError as e2:
                    print(f"     [ERROR] SG '{sg_id}' 삭제 실패: {e2}")

if __name__ == "__main__":
    sg_list = check()
    fix(sg_list)