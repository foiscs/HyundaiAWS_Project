#  4.operation/4_1_ebs_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.1] EBS 및 볼륨 암호화 설정
    - 리전의 기본 암호화 설정 여부와 암호화되지 않은 EBS 볼륨 존재 여부를 점검
    """
    print("[INFO] 4.1 EBS 및 볼륨 암호화 설정 체크 중...")
    findings = {'non_default_regions': [], 'unencrypted_volumes': []}
    
    try:
        ec2_regions = [r['RegionName'] for r in boto3.client('ec2').describe_regions()['Regions']]
        for region in ec2_regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                if not ec2.get_ebs_encryption_by_default()['EbsEncryptionByDefault']:
                    findings['non_default_regions'].append(region)
                
                paginator = ec2.get_paginator('describe_volumes')
                for page in paginator.paginate(Filters=[{'Name': 'status', 'Values': ['available', 'in-use']}]):
                    for vol in page['Volumes']:
                        if not vol.get('Encrypted'):
                            findings['unencrypted_volumes'].append({'id': vol['VolumeId'], 'region': region})
            except ClientError as e:
                if "OptInRequired" not in str(e): print(f"[ERROR] 리전 '{region}' 점검 중 오류: {e}")
        
        if findings['non_default_regions']:
            print(f"[⚠ WARNING] 4.1 기본 EBS 암호화가 비활성화된 리전: {', '.join(findings['non_default_regions'])}")
        if findings['unencrypted_volumes']:
            print(f"[⚠ WARNING] 4.1 암호화되지 않은 EBS 볼륨이 존재합니다 ({len(findings['unencrypted_volumes'])}개).")
            for v in findings['unencrypted_volumes']: print(f"  ├─ {v['id']} ({v['region']})")
        else:
            print("[✓ INFO] 4.1 암호화되지 않은 EBS 볼륨이 존재하지 않습니다.")
        
        if not findings['non_default_regions'] and not findings['unencrypted_volumes']:
            print("[✓ COMPLIANT] 4.1 모든 리전의 기본 암호화가 활성화되어 있고, 암호화되지 않은 볼륨이 없습니다.")
            
        return findings

    except ClientError as e:
        print(f"[ERROR] EBS 점검 중 오류 발생: {e}")
        return findings

def fix(findings):
    """
    [4.1] EBS 및 볼륨 암호화 설정 조치
    - 기본 암호화 활성화, 미암호화 볼륨은 수동 조치 안내
    """
    if not findings['non_default_regions'] and not findings['unencrypted_volumes']: return

    if findings['non_default_regions']:
        print("[FIX] 4.1 기본 EBS 암호화 설정 조치를 시작합니다.")
        for region in findings['non_default_regions']:
            if input(f"  -> 리전 '{region}'에 기본 EBS 암호화를 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    boto3.client('ec2', region_name=region).enable_ebs_encryption_by_default()
                    print(f"     [SUCCESS] 리전 '{region}'의 기본 암호화를 활성화했습니다.")
                except ClientError as e: print(f"     [ERROR] 실패: {e}")
    
    if findings['unencrypted_volumes']:
        print("[FIX] 4.1 기존의 암호화되지 않은 볼륨은 직접적인 암호화가 불가능하여 수동 조치가 필요합니다.")
        print("  └─ 1. 암호화되지 않은 볼륨의 스냅샷을 생성합니다.")
        print("  └─ 2. 생성된 스냅샷을 '암호화' 옵션을 사용하여 복사합니다.")
        print("  └─ 3. 암호화된 스냅샷으로부터 새 볼륨을 생성합니다.")
        print("  └─ 4. EC2 인스턴스에서 기존 볼륨을 분리(detach)하고 새로 생성한 암호화된 볼륨을 연결(attach)합니다.")

if __name__ == "__main__":
    findings_dict = check()
    fix(findings_dict)