import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

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
            return

        non_compliant_clusters = []
        for cluster_name in clusters:
            try:
                response = eks.describe_cluster(name=cluster_name)
                logging_config = response.get('cluster', {}).get('logging', {}).get('clusterLogging', [])
                
                enabled_log_types = set()
                if logging_config:
                    for log_info in logging_config:
                        if log_info.get('enabled'):
                            enabled_log_types.update(log_info.get('types', []))
                
                # 최소한 audit 로그는 있어야 함
                if 'audit' not in enabled_log_types:
                    non_compliant_clusters.append(f"{cluster_name} (활성 로그: {enabled_log_types or '없음'})")
            except ClientError as e:
                print(f"[ERROR] 클러스터 '{cluster_name}' 정보 확인 중 오류: {e}")

        if not non_compliant_clusters:
            print("[✓ COMPLIANT] 4.14 모든 EKS 클러스터에 제어 플레인 로깅(Audit)이 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.14 감사(Audit) 로그가 비활성화된 EKS 클러스터가 존재합니다 ({len(non_compliant_clusters)}개).")
            for finding in non_compliant_clusters:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 EKS 클러스터의 [로깅] 탭에서 Audit, API Server 등 필요한 제어 플레인 로그를 활성화하여 가시성을 확보하세요.")

    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")