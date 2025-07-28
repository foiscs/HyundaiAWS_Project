import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.4] 라우팅 테이블 정책 관리
    - 서브넷이 퍼블릭이 아님에도 0.0.0.0/0 경로(ANY 정책)가 라우팅 테이블에 존재하는 경우 취약
    """
    print("[INFO] 3.4 라우팅 테이블 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    misconfigured_routes = []

    try:
        # 1. 서브넷 정보 수집: 퍼블릭 IP 자동 할당 여부
        subnet_map = {
            s['SubnetId']: s.get('MapPublicIpOnLaunch', False)
            for s in ec2.describe_subnets()['Subnets']
        }

        # 2. 라우팅 테이블 반복
        for rt in ec2.describe_route_tables()['RouteTables']:
            rt_id = rt['RouteTableId']
            routes = rt.get('Routes', [])
            associations = rt.get('Associations', [])

            # 3. 0.0.0.0/0 대상 경로 추출
            any_route = next(
                (r for r in routes if r.get('DestinationCidrBlock') == '0.0.0.0/0'),
                None
            )

            if not any_route:
                continue  # ANY 경로 없으면 다음 RT로

            # 4. 연결된 서브넷들 중 퍼블릭이 아닌 경우 취약으로 분류
            for assoc in associations:
                subnet_id = assoc.get('SubnetId')
                if not subnet_id:
                    continue  # main route table인 경우 무시

                is_public = subnet_map.get(subnet_id, False)
                if not is_public:
                    # 퍼블릭이 아닌데 ANY 경로 존재함 → 취약
                    target = any_route.get('GatewayId') or any_route.get('NatGatewayId') or "UnknownTarget"
                    misconfigured_routes.append({
                        "RouteTableId": rt_id,
                        "SubnetId": subnet_id,
                        "Target": target
                    })

        # 5. 결과 출력
        if not misconfigured_routes:
            print("[✓ COMPLIANT] 3.4 라우팅 테이블에 잘못된 ANY 정책이 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 3.4 잘못된 ANY(0.0.0.0/0) 경로가 존재합니다 ({len(misconfigured_routes)}건).")
            for m in misconfigured_routes:
                print(f"  ├─ 프라이빗 서브넷 '{m['SubnetId']}' → 라우팅 테이블 '{m['RouteTableId']}'에 ANY 경로 (→ {m['Target']}) 존재")

        return misconfigured_routes

    except ClientError as e:
        print(f"[ERROR] 정보 수집 중 오류 발생: {e}")
        return []

def fix(misconfigured_routes):
    """
    [3.4] 라우팅 테이블 정책 관리 조치
    - 자동 수정은 위험하므로 가이드 제공
    """
    if not misconfigured_routes:
        return

    print("[FIX] 3.4 자동 조치는 지원하지 않습니다. 다음을 수동으로 조치하세요:")
    print("  └─ 1. 문제 서브넷의 라우팅 테이블에서 0.0.0.0/0 경로가 있는지 확인")
    print("  └─ 2. IGW 대신 NAT GW 또는 적절한 타깃으로 수정")
    print("  └─ 3. 필요 시 해당 서브넷을 퍼블릭 서브넷으로 전환하거나 라우팅 테이블 변경")

if __name__ == "__main__":
    rt_list = check()
    fix(rt_list)
