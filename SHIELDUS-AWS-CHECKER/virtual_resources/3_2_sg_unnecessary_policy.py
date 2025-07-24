import boto3
from botocore.exceptions import ClientError

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

def can_delete_sg(ec2, sg_id):
    try:
        ec2.delete_security_group(GroupId=sg_id)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'DependencyViolation':
            return False
        elif e.response['Error']['Code'] == 'InvalidGroup.NotFound':
            return False
        else:
            return True  # 기타 오류는 사용자 입력에 위임

def check():
    print("[INFO] 3.2 보안 그룹 인/아웃바운드 불필요 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    deletable = []

    try:
        all_sgs = ec2.describe_security_groups()['SecurityGroups']

        for sg in all_sgs:
            sg_id = sg['GroupId']
            sg_name = sg.get('GroupName', 'N/A')

            # ANY IP 규칙 포함 여부 확인
            matched = any(
                any(ip.get('CidrIp') == '0.0.0.0/0' for ip in rule.get('IpRanges', [])) or
                any(ip.get('CidrIpv6') == '::/0' for ip in rule.get('Ipv6Ranges', []))
                for rule in sg.get('IpPermissions', []) + sg.get('IpPermissionsEgress', [])
            )
            if not matched:
                continue

            if sg_name == 'default':
                print(f"  -> SG '{sg_id}' ({sg_name})는 기본 보안 그룹입니다. 삭제 대상이 아닙니다.")
                continue

            in_use, used_by = is_sg_in_use(ec2, sg_id)
            if in_use:
                print(f"  -> SG '{sg_id}' ({sg_name})는 리소스({used_by})에 의해 사용 중입니다. 삭제 대상이 아닙니다.")
                continue

            if not can_delete_sg(ec2, sg_id):
                print(f"  -> SG '{sg_id}' ({sg_name})는 다른 리소스에 의해 참조 중이라 삭제 대상이 아닙니다.")
                continue

            print(f"  -> SG '{sg_id}' ({sg_name})는 미연결 상태이며 ANY IP가 포함된 규칙이 존재합니다.")
            deletable.append({'GroupId': sg_id, 'GroupName': sg_name})

        if deletable:
            print(f"[!] 삭제 가능한 보안 그룹 {len(deletable)}개가 발견되었습니다.")
        else:
            print("[ⓘ info] 삭제 가능한 보안 그룹이 없습니다.")

        return deletable

    except ClientError as e:
        print(f"[ERROR] 보안 그룹 점검 중 오류 발생: {e}")
        return []

def fix(unused_sgs):
    if not unused_sgs:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.2 삭제 가능한 보안 그룹에 대해 사용자 동의를 받고 삭제합니다.")

    for sg in unused_sgs:
        sg_id = sg['GroupId']
        sg_name = sg['GroupName']

        print(f"  -> SG '{sg_id}' ({sg_name})를 삭제하시겠습니까? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print(f"     [SKIPPED] SG '{sg_id}' 삭제를 건너뜁니다.")
            continue

        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"     [SUCCESS] SG '{sg_id}'를 삭제했습니다.")
        except ClientError as e:
            print(f"     [ERROR] SG '{sg_id}' 삭제 실패: {e}")

if __name__ == "__main__":
    sg_list = check()
    fix(sg_list)