import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.8] RDS 서브넷 가용 영역 관리
    - RDS DB 서브넷 그룹이 2개 미만의 가용 영역(AZ)을 사용하여 구성되었는지 점검하고, 해당 그룹 목록 반환
    """
    print("[INFO] 3.8 RDS 서브넷 가용 영역 관리 체크 중...")
    rds = boto3.client('rds')
    single_az_subnet_groups = []

    try:
        for group in rds.describe_db_subnet_groups()['DBSubnetGroups']:
            if len({subnet['SubnetAvailabilityZone']['Name'] for subnet in group['Subnets']}) < 2:
                single_az_subnet_groups.append(group['DBSubnetGroupName'])

        if not single_az_subnet_groups:
            print("[✓ COMPLIANT] 3.8 모든 RDS DB 서브넷 그룹이 Multi-AZ로 구성되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 3.8 Single-AZ로 구성된 DB 서브넷 그룹이 존재합니다 ({len(single_az_subnet_groups)}개).")
            print(f"  ├─ 해당 서브넷 그룹: {', '.join(single_az_subnet_groups)}")
        
        return single_az_subnet_groups

    except ClientError as e:
        print(f"[ERROR] RDS DB 서브넷 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(single_az_subnet_groups):
    """
    [3.8] RDS 서브넷 가용 영역 관리 조치
    - 자동 조치 불가, 수동 조치 안내
    """
    if not single_az_subnet_groups:
        return

    print("[FIX] 3.8 DB 서브넷 그룹 수정은 VPC 네트워크 구조에 대한 이해가 필요하므로 자동화할 수 없습니다.")
    print("  └─ 고가용성을 위해 RDS 콘솔에서 아래 서브넷 그룹을 수동으로 편집하세요.")
    for group_name in single_az_subnet_groups:
        print(f"  └─ 1. RDS 콘솔 > [서브넷 그룹] > '{group_name}' 선택 후 [편집]을 클릭합니다.")
        print("  └─ 2. [서브넷 추가] 섹션에서 현재 그룹에 없는 다른 가용 영역(AZ)의 서브넷을 추가한 후 저장합니다.")

if __name__ == "__main__":
    group_list = check()
    fix(group_list)