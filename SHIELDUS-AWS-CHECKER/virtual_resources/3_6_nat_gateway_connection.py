import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.6] NAT 게이트웨이 연결 관리
    - NAT 게이트웨이의 연결 상태 출력
    - 라우팅 테이블에서 사용되지 않는 NAT 게이트웨이를 식별하여 리스트로 반환
    """
    print("[INFO] 3.6 NAT 게이트웨이 연결 현황 점검 중...")
    print("[ⓘ MANUAL] NAT 게이트웨이에 연결된 리소스가 외부 통신 필요 목적이 분명한지 판단할 수 없음")
    ec2 = boto3.client('ec2')
    unused_nat_ids = []

    try:
        # NAT 게이트웨이 조회
        nat_gateways = ec2.describe_nat_gateways(
            Filter=[{'Name': 'state', 'Values': ['pending', 'available']}]
        )['NatGateways']

        if not nat_gateways:
            print("[info] NAT 게이트웨이가 존재하지 않습니다.")
            return []

        # 라우팅 테이블 수집
        route_tables = ec2.describe_route_tables()['RouteTables']

        print("\n[NAT 게이트웨이 연결 현황]")
        for nat in nat_gateways:
            nat_id = nat['NatGatewayId']
            subnet_id = nat.get('SubnetId', 'Unknown')
            vpc_id = nat.get('VpcId', 'Unknown')
            state = nat['State']
            name_tag = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), 'NoName')

            print(f"\n- NAT Gateway ID: {nat_id}")
            print(f"  이름: {name_tag}, 상태: {state}, VPC: {vpc_id}, Subnet: {subnet_id}")

            used = False
            for rt in route_tables:
                for route in rt.get('Routes', []):
                    if route.get('NatGatewayId') == nat_id:
                        used = True
                        print(f"  ⮡ 라우팅 테이블 '{rt['RouteTableId']}'에서 사용 중")
                        break

            if not used:
                print("  ⚠️  사용되지 않음 (라우팅 테이블 연결 없음)")
                unused_nat_ids.append(nat_id)

        if not unused_nat_ids:
            print("\n[✓ COMPLIANT] 모든 NAT 게이트웨이가 사용 중입니다.")
        else:
            print(f"\n[⚠ WARNING] 사용되지 않는 NAT 게이트웨이가 {len(unused_nat_ids)}개 존재합니다.")
            print("  ⮡ 대상:", ", ".join(unused_nat_ids))

        return unused_nat_ids

    except ClientError as e:
        print(f"[ERROR] NAT 게이트웨이 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(unused_nat_ids):
    """
    [3.6] 미사용 NAT 게이트웨이에 대한 삭제 여부 확인 후 삭제
    """
    if not unused_nat_ids:
        return

    ec2 = boto3.client('ec2')
    print("\n[FIX] 사용되지 않는 NAT 게이트웨이에 대한 조치를 시작합니다.")

    for nat_id in unused_nat_ids:
        choice = input(f"  -> NAT 게이트웨이 '{nat_id}'를 삭제하시겠습니까? (삭제 전까지 비용 발생) (y/n): ").lower()
        if choice == 'y':
            try:
                ec2.delete_nat_gateway(NatGatewayId=nat_id)
                print(f"     [SUCCESS] NAT 게이트웨이 '{nat_id}' 삭제 요청 완료")
            except ClientError as e:
                print(f"     [ERROR] 삭제 실패: {e}")
        else:
            print(f"     [INFO] NAT 게이트웨이 '{nat_id}' 삭제를 건너뜁니다.")

if __name__ == "__main__":
    nat_list = check()
    fix(nat_list)
