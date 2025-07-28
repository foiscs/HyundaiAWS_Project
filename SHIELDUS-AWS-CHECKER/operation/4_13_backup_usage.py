#  4.operation/4_13_backup_usage.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.13] 백업 사용 여부
    - AWS Backup 플랜 존재 여부와 RDS 자동 백업 활성화 여부를 점검
    """
    print("[INFO] 4.13 백업 사용 여부 체크 중...")
    findings = {'no_backup_plan': True, 'rds_no_backup': [], 'rds_checked': False}
    
    try:
        if boto3.client('backup').list_backup_plans()['BackupPlansList']:
            findings['no_backup_plan'] = False
            print("[✓ COMPLIANT] 4.13 AWS Backup 플랜이 존재합니다.")
        else:
            print("[⚠ WARNING] 4.13 AWS Backup 플랜이 존재하지 않습니다. (EBS, EFS 등 점검 필요)")
    except ClientError as e:
        print(f"[ERROR] AWS Backup 점검 중 오류: {e}")
    
    try:
        rds_client = boto3.client('rds')
        dbs = rds_client.describe_db_instances()['DBInstances']
        if not dbs:
            print("[INFO] RDS 인스턴스가 존재하지 않습니다.")
        else:
            findings['rds_checked'] = True
            for inst in dbs:
                if inst.get('BackupRetentionPeriod', 0) == 0:
                    findings['rds_no_backup'].append(inst['DBInstanceIdentifier'])
            if findings['rds_no_backup']:
                print(f"[⚠ WARNING] 4.13 자동 백업이 비활성화된 RDS DB 인스턴스가 존재합니다: {findings['rds_no_backup']}")
            else:
                print("[✓ COMPLIANT] 4.13 모든 RDS 인스턴스에 자동 백업이 활성화되어 있습니다.")
    except ClientError as e:
        print(f"[ERROR] RDS 점검 중 오류: {e}")
        
    return findings

def fix(findings):
    """
    [4.13] 백업 사용 여부 조치
    - RDS 자동 백업 활성화, AWS Backup은 수동 안내
    """
    if not findings['no_backup_plan'] and not findings['rds_no_backup']: return

    if findings['no_backup_plan']:
        print("[FIX] 4.13 AWS Backup 플랜 생성은 백업 주기, 보관 정책 등 상세 설정이 필요하여 수동 조치를 권장합니다.")
        print("  └─ AWS Backup 콘솔에서 [백업 플랜 생성]을 통해 EBS, EFS, DynamoDB 등 중요 리소스에 대한 백업을 구성하세요.")

    if findings['rds_checked'] and findings['rds_no_backup']:
        rds = boto3.client('rds')
        print("[FIX] 4.13 RDS 자동 백업 설정 조치를 시작합니다.")
        for name in findings['rds_no_backup']:
            if input(f"  -> 인스턴스 '{name}'에 자동 백업을 활성화하시겠습니까? (y/n): ").lower() == 'y':
                try:
                    retention_period = int(input("     → 설정할 백업 보존 기간(일)을 입력하세요 (권장: 7 이상): ") or "7")
                    apply_now = input("     → 설정을 즉시 적용하시겠습니까? (일부 설정은 인스턴스 재시작을 유발할 수 있습니다) (y/n): ").lower()
                    apply_immediately = (apply_now == 'y')
                    
                    rds.modify_db_instance(
                        DBInstanceIdentifier=name,
                        BackupRetentionPeriod=retention_period,
                        ApplyImmediately=apply_immediately
                    )
                    print(f"     [SUCCESS] '{name}' 자동 백업 설정 요청 완료 ({'수 분 내 적용됨()' if apply_immediately else '다음 유지관리 시 적용됨'}).")
                except ClientError as e:
                    print(f"     [ERROR] 수정 실패: {e}")


if __name__ == "__main__":
    findings_dict = check()
    fix(findings_dict)
