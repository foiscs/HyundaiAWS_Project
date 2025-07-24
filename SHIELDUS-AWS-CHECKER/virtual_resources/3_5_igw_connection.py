import boto3
from botocore.exceptions import ClientError

def check():
    """
    [3.5] 인터넷 게이트웨이 연결 관리
    - 어떤 VPC에도 연결되지 않은 'detached' 상태의 인터넷 게이트웨이를 점검하고, 해당 ID 및 이름 목록 반환
    """
    print("[INFO] 3.5 인터넷 게이트웨이 연결 관리 체크 중...")
    ec2 = boto3.client('ec2')
    detached_igws = []

    try:
        for igw in ec2.describe_internet_gateways()['InternetGateways']:
            # Attachments 배열이 비어 있으면 detached 상태
            if not igw.get('Attachments'):
                igw_id = igw['InternetGatewayId']
                # Name 태그 추출 (없으면 '( - )' 표시)
                tags = igw.get('Tags', [])
                name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), "( - )")

                # IGW ID와 이름을 함께 저장
                detached_igws.append({
                    "InternetGatewayId": igw_id,
                    "Name": name
                })

        if not detached_igws:
            print("[✓ COMPLIANT] 3.5 모든 인터넷 게이트웨이가 VPC에 정상적으로 연결되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 3.5 VPC에 연결되지 않은 불필요한 인터넷 게이트웨이가 존재합니다 ({len(detached_igws)}개).")
            for igw in detached_igws:
                print(f"  ├─ IGW ID: {igw['InternetGatewayId']} (이름: {igw['Name']})")

        return detached_igws

    except ClientError as e:
        print(f"[ERROR] 인터넷 게이트웨이 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(detached_igws):
    """
    [3.5] 인터넷 게이트웨이 연결 관리 조치
    - 미사용 IGW를 사용자 확인 후 삭제
    """
    if not detached_igws:
        return

    ec2 = boto3.client('ec2')
    print("[FIX] 3.5 연결되지 않은 인터넷 게이트웨이에 대한 조치를 시작합니다.")
    for igw in detached_igws:
        igw_id = igw['InternetGatewayId']
        name = igw['Name']
        choice = input(f"  -> 미사용 인터넷 게이트웨이 '{igw_id}' (이름: {name})를 삭제하시겠습니까? (y/n): ").lower()
        if choice == 'y':
            try:
                ec2.delete_internet_gateway(InternetGatewayId=igw_id)
                print(f"     [SUCCESS] IGW '{igw_id}' (이름: {name})를 삭제했습니다.")
            except ClientError as e:
                print(f"     [ERROR] IGW '{igw_id}' 삭제 실패: {e}")
        else:
            print(f"     [INFO] IGW '{igw_id}' 삭제를 건너뜁니다.")

if __name__ == "__main__":
    igw_list = check()
    fix(igw_list)
