import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [4.13] 백업 사용 여부
    - AWS Backup 플랜이 존재하는지, RDS 자동 백업이 활성화되었는지 점검
    """
    print("[INFO] 4.13 백업 사용 여부 체크 중...")
    
    # 1. AWS Backup 플랜 점검
    backup = boto3.client('backup')
    is_backup_plan_ok = False
    try:
        backup_plans = backup.list_backup_plans().get('BackupPlansList', [])
        if backup_plans:
            print(f"[✓ COMPLIANT] 4.13 AWS Backup 플랜이 존재합니다 ({len(backup_plans)}개).")
            is_backup_plan_ok = True
        else:
            print("[⚠ WARNING] 4.13 AWS Backup 플랜이 존재하지 않습니다.")
    except ClientError as e:
        print(f"[ERROR] AWS Backup 정보를 가져오는 중 오류 발생: {e}")

    # 2. RDS 자동 백업 점검
    rds = boto3.client('rds')
    rds_no_backup = []
    is_rds_ok = True
    try:
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                if instance.get('BackupRetentionPeriod', 0) == 0:
                    rds_no_backup.append(instance['DBInstanceIdentifier'])
        
        if rds_no_backup:
            is_rds_ok = False
            print(f"[⚠ WARNING] 4.13 자동 백업이 비활성화된 RDS DB 인스턴스가 존재합니다 ({len(rds_no_backup)}개).")
            print(f"  ├─ 해당 인스턴스: {', '.join(rds_no_backup)}")
    except ClientError as e:
        print(f"[ERROR] RDS 정보를 가져오는 중 오류 발생: {e}")

    if is_backup_plan_ok and is_rds_ok:
         print("[✓ COMPLIANT] 4.13 전반적인 백업 정책이 설정되어 있습니다. (세부 내용은 수동 확인 필요)")
    else:
         print("  └─ 🔧 AWS Backup, RDS 자동 백업, EBS 스냅샷 정책 등을 활용하여 중요 데이터의 백업 및 복구 절차를 수립하세요.")