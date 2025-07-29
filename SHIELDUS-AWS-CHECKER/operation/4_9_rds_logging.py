# 4.operation/4_9_rds_logging.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.9] RDS 로깅 설정 점검 - PostgreSQL & MySQL
    - PostgreSQL 계열: postgresql
    - MySQL 계열: error, slowquery, general, audit
    - iam-db-auth-error는 제외
    """
    print("[INFO] 4.9 RDS 로깅 설정 점검 중...")
    rds = boto3.client('rds')
    insufficient_logging_instances = {}

    try:
        insts = rds.describe_db_instances()['DBInstances']
        if not insts:
            print("[INFO] 4.9 확인할 RDS 인스턴스가 존재하지 않습니다.")
            return {}

        for inst in insts:
            db_id = inst['DBInstanceIdentifier']
            engine = inst['Engine']
            enabled_logs = inst.get('EnabledCloudwatchLogsExports', [])

            # 점검 대상 로그 설정
            if 'postgres' in engine:
                required_logs = ['postgresql']
            elif 'mysql' in engine:
                required_logs = ['error', 'slowquery', 'general', 'audit']
            else:
                continue  # 비대상 엔진은 건너뜀

            missing_logs = [log for log in required_logs if log not in enabled_logs]
            if missing_logs:
                insufficient_logging_instances[db_id] = missing_logs

        if not insufficient_logging_instances:
            print("[✓ COMPLIANT] 4.9 모든 RDS 인스턴스에 로그 내보내기가 적절히 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.9 로그 미설정 RDS 인스턴스 발견 ({len(insufficient_logging_instances)}개).")
            for name, logs in insufficient_logging_instances.items():
                print(f"  ├─ {name} (필요 로그: {', '.join(logs)})")

        return insufficient_logging_instances

    except ClientError as e:
        print(f"[ERROR] RDS 정보를 가져오는 중 오류 발생: {e}")
        return {}

def fix(insufficient_logging_instances):
    """
    [4.9] RDS 로깅 설정 조치 - PostgreSQL & MySQL
    """
    if not insufficient_logging_instances:
        return

    rds = boto3.client('rds')
    print("[FIX] 4.9 RDS 로그 설정 조치 시작합니다.")
    for name, missing_logs in insufficient_logging_instances.items():
        if input(f"  -> 인스턴스 '{name}'에 로그({', '.join(missing_logs)}) 내보내기를 활성화하시겠습니까? (y/n): ").lower() == 'y':
            try:
                current_logs = rds.describe_db_instances(DBInstanceIdentifier=name)['DBInstances'][0].get('EnabledCloudwatchLogsExports', [])
                all_logs_to_enable = list(set(current_logs + missing_logs))

                rds.modify_db_instance(
                    DBInstanceIdentifier=name,
                    CloudwatchLogsExportConfiguration={'EnableLogTypes': all_logs_to_enable},
                    ApplyImmediately=False
                )
                print(f"     [SUCCESS] '{name}' 로그 설정 수정 요청 완료 (즉시 또는 유지관리 윈도우에 반영됩니다).")
            except ClientError as e:
                print(f"     [ERROR] 인스턴스 수정 실패: {e}")

if __name__ == "__main__":
    instances = check()
    fix(instances)
