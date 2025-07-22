import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [4.1] EBS 및 볼륨 암호화 설정
    - 암호화되지 않은 EBS 볼륨이 있는지, 리전의 기본 암호화 설정이 활성화되어 있는지 점검
    """
    print("[INFO] 4.1 EBS 및 볼륨 암호화 설정 체크 중...")
    
    # 각 리전별로 점검
    ec2_regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]
    all_unencrypted_volumes = []
    non_default_encrypted_regions = []

    for region in ec2_regions:
        try:
            ec2 = boto3.client('ec2', region_name=region)
            
            # 1. 기본 암호화 설정 점검
            if not ec2.get_ebs_encryption_by_default()['EbsEncryptionByDefault']:
                non_default_encrypted_regions.append(region)

            # 2. 개별 볼륨 암호화 점검
            paginator = ec2.get_paginator('describe_volumes')
            for page in paginator.paginate(Filters=[{'Name': 'status', 'Values': ['available', 'in-use']}]):
                for volume in page['Volumes']:
                    if not volume.get('Encrypted'):
                        all_unencrypted_volumes.append(f"{volume['VolumeId']} ({region}, 상태: {volume['State']})")
        except ClientError as e:
            if "AuthFailure" in str(e) or "OptInRequired" in str(e):
                continue # 활성화되지 않은 리전은 건너뜀
            else:
                print(f"[ERROR] 리전 '{region}' 점검 중 오류 발생: {e}")

    if not non_default_encrypted_regions:
        print("[✓ COMPLIANT] 4.1 모든 점검된 리전의 기본 EBS 암호화가 활성화되어 있습니다.")
    else:
        print(f"[⚠ WARNING] 4.1 기본 EBS 암호화가 비활성화된 리전이 있습니다: {', '.join(non_default_encrypted_regions)}")
        print("  └─ 🔧 EC2 대시보드 > 설정 > EBS 암호화에서 기본 암호화를 활성화하세요.")

    if not all_unencrypted_volumes:
        print("[✓ COMPLIANT] 4.1 암호화되지 않은 EBS 볼륨이 없습니다.")
    else:
        print(f"[⚠ WARNING] 4.1 암호화되지 않은 EBS 볼륨이 존재합니다 ({len(all_unencrypted_volumes)}개).")
        for vol_info in all_unencrypted_volumes:
            print(f"  ├─ {vol_info}")
        print("  └─ 🔧 데이터를 백업하고 암호화된 볼륨으로 마이그레이션하세요.")