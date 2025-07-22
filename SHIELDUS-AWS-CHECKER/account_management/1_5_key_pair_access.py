import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.5] Key Pair 접근 관리
    - 실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 있는지 점검하고, 없는 인스턴스 목록 반환
    """
    print("[INFO] 1.5 Key Pair 접근 관리 체크 중...")
    ec2 = boto3.client('ec2')
    instances_without_keypair = []

    try:
        paginator = ec2.get_paginator('describe_instances')
        pages = paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        for page in pages:
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    if 'KeyName' not in instance:
                        instances_without_keypair.append(instance['InstanceId'])

        if not instances_without_keypair:
            print("[✓ COMPLIANT] 1.5 실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 1.5 Key Pair 없이 실행 중인 EC2 인스턴스가 존재합니다 ({len(instances_without_keypair)}개).")
            print(f"  ├─ 해당 인스턴스: {', '.join(instances_without_keypair)}")
        
        return instances_without_keypair

    except ClientError as e:
        print(f"[ERROR] EC2 인스턴스 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(instances_without_keypair):
    """
    [1.5] Key Pair 접근 관리 조치
    - Key Pair 할당은 인스턴스 재시작 또는 재배포가 필요하므로 자동 조치가 불가능함. 수동 조치 안내
    """
    if not instances_without_keypair:
        return
        
    print("[FIX] 1.5 Key Pair가 없는 인스턴스에 대한 조치는 자동화할 수 없습니다.")
    print("  └─ 실행 중인 인스턴스에 Key Pair를 추가하는 것은 직접적인 방법이 없으므로 아래의 수동 절차를 따르세요.")
    print("  └─ 1. 해당 인스턴스의 AMI(Amazon Machine Image)를 생성합니다.")
    print("  └─ 2. 생성한 AMI를 사용하여 새 인스턴스를 시작할 때, 새로운 Key Pair를 지정합니다.")
    print("  └─ 3. 데이터 및 설정을 마이그레이션한 후, 기존 인스턴스를 종료합니다.")
    print("  └─ 또는, Systems Manager Session Manager를 사용하여 Key Pair 없이 안전하게 접근하는 방법을 고려하세요.")

if __name__ == "__main__":
    instance_list = check()
    fix(instance_list)