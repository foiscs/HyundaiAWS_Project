import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.8] RDS 서브넷 가용 영역 관리 (수동 진단)
    - 각 RDS DB 서브넷 그룹이 어떤 가용 영역(AZ)들로 구성되어 있는지 정보를 출력하여 관리자가 직접 판단하도록 안내
    """
    print("[INFO] 3.8 RDS 서브넷 가용 영역 관리 체크 중...")
    rds = boto3.client('rds')
    subnet_groups_to_review = []

    try:
        response = rds.describe_db_subnet_groups()
        if not response['DBSubnetGroups']:
            print("[✓ COMPLIANT] 3.8 점검할 RDS DB 서브넷 그룹이 없습니다.")
            return []

        print("[ⓘ MANUAL] 이 항목은 수동 진단이 필요합니다. 각 서브넷 그룹의 가용 영역 구성을 검토하세요.")
        print("-" * 40)
        
        for group in response['DBSubnetGroups']:
            group_name = group['DBSubnetGroupName']
            # 각 서브넷의 가용 영역(AZ)을 추출하여 중복을 제거하고 정렬
            az_set = {subnet['SubnetAvailabilityZone']['Name'] for subnet in group['Subnets']}
            az_list_sorted = sorted(list(az_set))
            
            # 관리자가 판단할 수 있도록 정보 출력
            print(f"  -> 서브넷 그룹: '{group_name}'")
            print(f"     └─ 사용 중인 가용 영역: {', '.join(az_list_sorted)} ({len(az_list_sorted)}개)")
            
            subnet_groups_to_review.append(group_name)

        print("-" * 40)
        print("  [양호 기준]: RDS 서브넷 그룹 내에 불필요한 가용 영역이 존재하지 않는 경우.")
        print("  [취약 기준]: RDS 서브넷 그룹 내에 불필요한 가용 영역이 존재하는 경우. (예: 특정 AZ의 서브넷은 더 이상 사용하지 않음)")
        
        # 모든 그룹에 대해 검토가 필요하므로 전체 목록을 반환
        return subnet_groups_to_review

    except ClientError as e:
        print(f"[ERROR] RDS DB 서브넷 그룹 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(subnet_group_names):
    """
    [3.8] RDS 서브넷 가용 영역 관리 조치
    - 서브넷 그룹 수정은 수동으로 진행하도록 상세히 안내
    """
    if not subnet_group_names:
        return

    print("[FIX] 3.8 DB 서브넷 그룹의 가용 영역 수정은 수동 조치가 필요합니다.")
    print("  └─ 1. AWS Management Console에서 RDS 서비스로 이동합니다.")
    print("  └─ 2. 왼쪽 메뉴에서 [서브넷 그룹]을 선택합니다.")
    print("  └─ 3. 수정이 필요한 서브넷 그룹(예: " + f"'{subnet_group_names[0]}'" + ")을 선택하고 [편집] 버튼을 클릭합니다.")
    print("  └─ 4. '서브넷 추가' 섹션에서 불필요한 가용 영역에 속한 서브넷을 선택 해제하거나, 필요한 서브넷을 추가합니다.")
    print("  └─ 5. [저장]을 클릭하여 변경 사항을 적용합니다.")

if __name__ == "__main__":
    group_list = check()
    fix(group_list)