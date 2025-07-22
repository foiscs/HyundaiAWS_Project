import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [1.5] Key Pair 접근 관리
    - 실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 있는지 점검
    - Key Pair가 없는 인스턴스는 패스워드 기반 접근 등 다른 방법을 사용할 수 있어 보안에 취약
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
            print("  └─ 🔧 인스턴스 접근 보안을 위해 Key Pair를 사용하도록 구성하세요.")
            print("  └─ 🔧 가이드: 신규 인스턴스 생성 시 Key Pair를 지정하거나, 기존 인스턴스는 AMI 생성 후 Key Pair를 지정하여 재배포하는 것을 권장합니다.")

    except ClientError as e:
        print(f"[-] [ERROR] EC2 인스턴스 정보를 가져오는 중 오류 발생: {e}")