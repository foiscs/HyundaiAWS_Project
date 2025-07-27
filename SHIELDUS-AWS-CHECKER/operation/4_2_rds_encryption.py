#  4.operation/4_2_rds_encryption.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.2] RDS 암호화 설정
    - 암호화되지 않은 RDS DB 인스턴스/클러스터를 점검하고 목록을 반환
    """
    print("[INFO] 4.2 RDS 암호화 설정 체크 중...")
    rds = boto3.client('rds')
    unencrypted_resources = []
    total_resources = 0  # 전체 리소스 수 추적

    try:
        # DB 인스턴스 점검
        instances = rds.describe_db_instances()['DBInstances']
        for inst in instances:
            total_resources += 1
            if not inst.get('StorageEncrypted'):
                unencrypted_resources.append(f"인스턴스: {inst['DBInstanceIdentifier']}")

        # DB 클러스터 점검
        clusters = rds.describe_db_clusters()['DBClusters']
        for cluster in clusters:
            total_resources += 1
            if not cluster.get('StorageEncrypted'):
                unencrypted_resources.append(f"클러스터: {cluster['DBClusterIdentifier']}")

        # 출력 분기 처리
        if total_resources == 0:
            print("[✓ INFO] 4.2 점검할 RDS 리소스가 존재하지 않습니다.")
        elif not unencrypted_resources:
            print("[✓ COMPLIANT] 4.2 모든 RDS 리소스가 암호화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.2 스토리지 암호화가 비활성화된 RDS 리소스가 존재합니다 ({len(unencrypted_resources)}개).")
            for res in unencrypted_resources:
                print(f"  ├─ {res}")
        return unencrypted_resources

    except ClientError as e:
        print(f"[ERROR] RDS 정보를 가져오는 중 오류 발생: {e}")
        return []
    
def fix(unencrypted_resources):
    """
    [4.2] RDS 암호화 설정 조치
    - 자동 조치 불가, 수동 마이그레이션 절차 안내
    """
    if not unencrypted_resources: return

    print("[FIX] 4.2 기존 RDS 리소스의 암호화는 직접 활성화할 수 없어 수동 조치가 필요합니다.")
    print("  └─ 아래의 일반적인 마이그레이션 절차를 따르세요.")
    print("  └─ 1. 암호화되지 않은 DB 인스턴스/클러스터의 최종 스냅샷을 생성합니다.")
    print("  └─ 2. 생성된 스냅샷을 '암호화' 옵션을 사용하여 복사합니다.")
    print("  └─ 3. 암호화된 스냅샷으로부터 새 DB 인스턴스/클러스터를 복원합니다.")
    print("  └─ 4. 애플리케이션의 DB 엔드포인트를 새로 생성한 리소스로 변경하고, 테스트 후 기존 리소스를 삭제합니다.")

if __name__ == "__main__":
    resources = check()
    fix(resources)