# 3.virtual_resources/3_4_route_table_policy.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.4] 라우팅 테이블 정책 관리
    - 프라이빗 서브넷의 라우팅 테이블에 IGW로 가는 경로가 있는지 점검
    - 퍼블릭 IP 자동 할당이 비활성화된 서브넷에 연결된 라우팅 테이블에 IGW 경로가 있으면 취약으로 간주
    """
    print("[INFO] 3.4 라우팅 테이블 정책 관리 체크 중...")
    ec2 = boto3.client('ec2')
    misconfigured_rts = []

    try:
        subnets = {s['SubnetId']: s.get('MapPublicIpOnLaunch', False) for s in ec2.describe_subnets()['Subnets']}
        for rt in ec2.describe_route_tables()['RouteTables']:
            has_igw_route = any(r.get('GatewayId', '').startswith('igw-') for r in rt.get('Routes', []))
            if has_igw_route:
                for assoc in rt.get('Associations', []):
                    subnet_id = assoc.get('SubnetId')
                    # 프라이빗 서브넷(Public IP 자동할당 X)이 IGW로 라우팅되는 경우
                    if subnet_id and not subnets.get(subnet_id, False):
                        misconfigured_rts.append(f"프라이빗 서브넷 '{subnet_id}'이(가) IGW 경로가 있는 라우팅 테이블 '{rt['RouteTableId']}'에 연결됨")
        
        if not misconfigured_rts:
            print("[✓ COMPLIANT] 3.4 라우팅 테이블 구성에 명백한 오류가 발견되지 않았습니다.")
        else:
            print(f"[⚠ WARNING] 3.4 잘못된 라우팅 정책이 의심되는 라우팅 테이블이 있습니다 ({len(misconfigured_rts)}건).")
            for finding in misconfigured_rts: print(f"  ├─ {finding}")
        
        return misconfigured_rts

    except ClientError as e:
        print(f"[ERROR] 라우팅 테이블/서브넷 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(misconfigured_rts):
    """
    [3.4] 라우팅 테이블 정책 관리 조치
    - 라우팅 변경은 매우 위험하므로 자동 조치 대신 수동 조치 가이드를 제공
    """
    if not misconfigured_rts:
        return

    print("[FIX] 3.4 라우팅 테이블 자동 조치는 네트워크 단절을 유발할 수 있어 지원하지 않습니다.")
    print("  └─ 프라이빗 서브넷은 NAT 게이트웨이를 사용하도록, 퍼블릭 서브넷은 인터넷 게이트웨이를 사용하도록 라우팅 경로를 수동으로 수정하세요.")
    print("  └─ 1. VPC 콘솔 > 라우팅 테이블로 이동합니다.")
    print("  └─ 2. 문제가 된 라우팅 테이블을 선택하고 [경로] 탭에서 IGW로 향하는 경로(0.0.0.0/0 -> igw-xxxx)를 편집하거나 삭제합니다.")
    print("  └─ 3. 또는, [서브넷 연결] 탭에서 해당 프라이빗 서브넷의 연결을 변경하여 NAT GW용 라우팅 테이블과 연결합니다.")

if __name__ == "__main__":
    rt_list = check()
    fix(rt_list)