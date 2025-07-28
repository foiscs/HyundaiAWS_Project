#  4.operation/4_14_eks_control_plane_logging.py
import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.14] EKS Cluster 제어 플레인 로깅 설정
    - 모든 EKS 클러스터에서 5개 로그(api, audit, authenticator, controllerManager, scheduler)가 활성화되어 있는지 점검
    """
    print("[INFO] 4.14 EKS Cluster 제어 플레인 로깅 설정 체크 중...")
    eks = boto3.client('eks')

    try:
        clusters = eks.list_clusters().get('clusters', [])
        if not clusters:
            print("[INFO] 4.14 점검할 EKS 클러스터가 없습니다.")
            return []

        required_logs = {'api', 'audit', 'authenticator', 'controllerManager', 'scheduler'}
        non_compliant_clusters = []

        for name in clusters:
            try:
                cluster_info = eks.describe_cluster(name=name)['cluster']
                if cluster_info.get('status') != 'ACTIVE':
                    print(f"[SKIP] 클러스터 '{name}'는 ACTIVE 상태가 아니므로 점검 제외.")
                    continue

                logging_config = cluster_info.get('logging', {}).get('clusterLogging', [])
                enabled_logs = {t for log in logging_config if log.get('enabled') for t in log.get('types', [])}
                missing = required_logs - enabled_logs

                if missing:
                    non_compliant_clusters.append({
                        'name': name,
                        'logs': list(enabled_logs),
                        'missing': list(missing)
                    })

            except ClientError as e:
                print(f"[ERROR] 클러스터 '{name}' 정보 확인 중 오류: {e}")

        if not non_compliant_clusters:
            print("[✓ COMPLIANT] 4.14 모든 EKS 클러스터의 제어 플레인 로그가 설정되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.14 제어 플레인 로그가 누락된 클러스터가 있습니다 ({len(non_compliant_clusters)}개):")
            for c in non_compliant_clusters:
                print(f"  ├─ {c['name']} (활성 로그: {c['logs'] or '없음'}) → 누락 로그: {c['missing']}")

        return non_compliant_clusters

    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")
        return []

def fix(non_compliant_clusters):
    """
    [4.14] EKS Cluster 제어 플레인 로깅 설정 조치
    - 비활성화된 로그가 있는 클러스터에 대해 모든 제어 플레인 로그(api, audit, authenticator, controllerManager, scheduler)를 활성화
    """
    if not non_compliant_clusters:
        print("[INFO] 조치할 클러스터가 없습니다.")
        return

    eks = boto3.client('eks')
    all_types = ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler']
    print("[FIX] 4.14 EKS 제어 플레인 로깅 활성화 조치를 시작합니다.")

    for cluster in non_compliant_clusters:
        name = cluster['name']
        current_logs = cluster['logs']
        missing_logs = cluster['missing']

        print(f"  ─ 클러스터 '{name}': 누락 로그 → {missing_logs}")
        proceed = input(f"     → 모든 로그를 활성화하시겠습니까? (y/n): ").strip().lower()
        if proceed != 'y':
            print(f"     [SKIPPED] '{name}' 조치를 건너뜁니다.")
            continue

        try:
            eks.update_cluster_config(
                name=name,
                logging={'clusterLogging': [{'types': all_types, 'enabled': True}]}
            )
            print(f"     [SUCCESS] 클러스터 '{name}'의 모든 제어 플레인 로그 활성화를 요청했습니다.")
        except ClientError as e:
            print(f"     [ERROR] 클러스터 '{name}' 설정 업데이트 실패: {e}")


if __name__ == "__main__":
    clusters = check()
    fix(clusters)