import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.9] RDS 로깅 설정
    - RDS DB 인스턴스에 주요 로그(audit, error, general, slowquery)가 활성화되어 있는지 점검
    """
    print("[INFO] 4.9 RDS 로깅 설정 체크 중...")
    rds = boto3.client('rds')
    insufficient_logging_instances = {}

    try:
        for inst in rds.describe_db_instances()['DBInstances']:
            enabled_logs = inst.get('EnabledCloudwatchLogsExports', [])
            # 최소한 error 로그와 audit(지원 시) 로그는 있어야 함
            if 'error' not in enabled_logs or 'audit' not in enabled_logs:
                 # Aurora-mysql/postgresql은 audit 지원
                if 'aurora' in inst['Engine'] and 'audit' not in enabled_logs:
                    insufficient_logging_instances[inst['DBInstanceIdentifier']] = ['audit', 'error']
                elif 'error' not in enabled_logs:
                    insufficient_logging_instances[inst['DBInstanceIdentifier']] = ['error']
        
        if not insufficient_logging_instances:
            print("[✓ COMPLIANT] 4.9 모든 RDS DB 인스턴스에 주요 로그가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.9 주요 로그(Error/Audit)가 활성화되지 않은 RDS DB 인스턴스가 존재합니다 ({len(insufficient_logging_instances)}개).")
            for name, logs in insufficient_logging_instances.items(): print(f"  ├─ {name} (필요 로그: {logs})")
        
        return insufficient_logging_instances

    except ClientError as e:
        print(f"[ERROR] RDS 정보를 가져오는 중 오류 발생: {e}")
        return {}

def fix(insufficient_logging_instances):
    """
    [4.9] RDS 로깅 설정 조치
    - 미활성화된 로그를 활성화하도록 인스턴스를 수정
    """
    if not insufficient_logging_instances: return

    rds = boto3.client('rds')
    print("[FIX] 4.9 RDS 로그 내보내기 설정 조치를 시작합니다.")
    for name, logs_to_enable in insufficient_logging_instances.items():
        if input(f"  -> 인스턴스 '{name}'에 로그({', '.join(logs_to_enable)}) 내보내기를 활성화하시겠습니까? (수정 사항 즉시 적용 시 재부팅될 수 있음) (y/n): ").lower() == 'y':
            try:
                # 기존 활성화된 로그도 함께 전달해야 함
                current_logs = rds.describe_db_instances(DBInstanceIdentifier=name)['DBInstances'][0].get('EnabledCloudwatchLogsExports', [])
                all_logs_to_enable = list(set(current_logs + logs_to_enable))
                
                rds.modify_db_instance(
                    DBInstanceIdentifier=name,
                    CloudwatchLogsExportConfiguration={'EnableLogTypes': all_logs_to_enable},
                    ApplyImmediately=False # 안전을 위해 즉시 적용 안함
                )
                print(f"     [SUCCESS] '{name}'에 대한 수정 요청을 보냈습니다. 다음 유지관리 기간에 적용됩니다.")
            except ClientError as e:
                print(f"     [ERROR] 인스턴스 수정 실패: {e}")

if __name__ == "__main__":
    instances = check()
    fix(instances)