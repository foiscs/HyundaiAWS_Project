import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.6] NAT 게이트웨이 연결 관리
    - 생성되었지만 어떤 라우팅 테이블에서도 사용되지 않는 NAT 게이트웨이를 점검하고, 해당 ID 목록 반환
    """
    print("[INFO] 3.6 NAT 게이트웨이 연결 관리 체크 중...")
    ec2 = boto3.client('ec2')
    
    try:
        # 'available' 또는 'pending' 상태의 모든 NAT GW ID 수집
        all_nat_ids = {
            nat['NatGatewayId'] for nat in ec2.describe_nat_gateways(
                Filter=[{'Name': 'state', 'Values': ['pending', 'available']}]
            )['NatGateways']
        }
        
        # 라우팅 테이블에서 사용 중인 NAT GW ID 수집
        used_nat_ids = set()
        for rt in ec2.describe_route_tables()['RouteTables']:
            for route in rt['Routes']:
                if route.get('NatGatewayId'):
                    used_nat_ids.add(route['NatGatewayId'])
        
        unused_nat_ids = list(all_nat_ids - used_nat_ids)

        if not unused_nat_ids:
            print("[✓ COMPLIANT] 3.6 모든 NAT 게이트웨이가 라우팅 테이블에서 사용 중입니다.")
        else:
            print(f"[⚠ WARNING] 3.6 라우팅 테이블에서 사용되지 않는 NAT 게이트웨이가 존재합니다 ({len(unused_nat_ids)}개).")
            print(f"  ├─ 해당 NAT GW: {', '.join(unused_nat_ids)}")
        
        return unused_nat_ids
        
    except ClientError as e:
        print(f"[ERROR] NAT 게이트웨이 또는 라우팅 테이블 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(unused_nat_ids):
    """
    [3.6] NAT 게이트웨이 연결 관리 조치
    - 미사용 NAT GW를 사용자 확인 후 삭제
    """
    if not unused_nat_ids:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.6 사용되지 않는 NAT 게이트웨이에 대한 조치를 시작합니다.")
    for nat_id in unused_nat_ids:
        choice = input(f"  -> 미사용 NAT 게이트웨이 '{nat_id}'를 삭제하시겠습니까? (삭제 전까지 비용 발생) (y/n): ").lower()
        if choice == 'y':
            try:
                ec2.delete_nat_gateway(NatGatewayId=nat_id)
                print(f"     [SUCCESS] NAT 게이트웨이 '{nat_id}'에 대한 삭제 요청을 보냈습니다. (상태가 'deleted'로 변경되기까지 시간이 걸릴 수 있습니다)")
            except ClientError as e:
                print(f"     [ERROR] NAT 게이트웨이 '{nat_id}' 삭제 실패: {e}")
        else:
            print(f"     [INFO] NAT 게이트웨이 '{nat_id}' 삭제를 건너뜁니다.")

if __name__ == "__main__":
    nat_list = check()
    fix(nat_list)