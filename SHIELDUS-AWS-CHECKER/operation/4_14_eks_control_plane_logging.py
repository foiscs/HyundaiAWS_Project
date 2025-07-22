import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.14] EKS Cluster 제어 플레인 로깅 설정
    - EKS 클러스터의 제어 플레인 로그(audit, api)가 활성화되어 있는지 점검
    """
    print("[INFO] 4.14 EKS Cluster 제어 플레인 로깅 설정 체크 중...")
    eks = boto3.client('eks')
    
    try:
        clusters = eks.list_clusters().get('clusters', [])
        if not clusters:
            print("[INFO] 4.14 점검할 EKS 클러스터가 없습니다.")
            return []

        non_compliant_clusters = []
        for name in clusters:
            try:
                logging_config = eks.describe_cluster(name=name)['cluster']['logging']['clusterLogging']
                enabled_logs = {t for log in logging_config if log.get('enabled') for t in log.get('types', [])}
                if 'audit' not in enabled_logs or 'api' not in enabled_logs:
                    non_compliant_clusters.append({'name': name, 'logs': list(enabled_logs)})
            except ClientError as e: print(f"[ERROR] 클러스터 '{name}' 정보 확인 중 오류: {e}")

        if not non_compliant_clusters:
            print("[✓ COMPLIANT] 4.14 모든 EKS 클러스터에 주요 제어 플레인 로깅이 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.14 주요 제어 플레인 로그(api, audit)가 비활성화된 EKS 클러스터가 있습니다 ({len(non_compliant_clusters)}개).")
            for c in non_compliant_clusters: print(f"  ├─ {c['name']} (활성 로그: {c['logs'] or '없음'})")
        
        return non_compliant_clusters

    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")
        return []

def fix(non_compliant_clusters):
    """
    [4.14] EKS Cluster 제어 플레인 로깅 설정 조치
    - 미활성화된 로그를 활성화
    """
    if not non_compliant_clusters: return

    eks = boto3.client('eks')
    print("[FIX] 4.14 EKS 제어 플레인 로깅 활성화 조치를 시작합니다.")
    for cluster in non_compliant_clusters:
        name = cluster['name']
        current_logs = cluster['logs']
        if input(f"  -> 클러스터 '{name}'에 api, audit 로그를 활성화하시겠습니까? (y/n): ").lower() == 'y':
            try:
                # 모든 로그 유형을 활성화하도록 설정
                all_types = ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler']
                eks.update_cluster_config(
                    name=name,
                    logging={'clusterLogging': [{'types': all_types, 'enabled': True}]}
                )
                print(f"     [SUCCESS] 클러스터 '{name}'의 모든 제어 플레인 로그 활성화 요청을 보냈습니다.")
            except ClientError as e:
                print(f"     [ERROR] 설정 업데이트 실패: {e}")

if __name__ == "__main__":
    clusters = check()
    fix(clusters)