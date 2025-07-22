import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.15] EKS Cluster 암호화 설정
    - EKS 클러스터의 시크릿(Secret)에 대한 봉투 암호화(envelope encryption)가 활성화되어 있는지 점검
    """
    print("[INFO] 4.15 EKS Cluster 암호화 설정 체크 중...")
    eks = boto3.client('eks')
    
    try:
        clusters = eks.list_clusters().get('clusters', [])
        if not clusters:
            print("[INFO] 4.15 점검할 EKS 클러스터가 없습니다.")
            return
            
        unencrypted_clusters = []
        for cluster_name in clusters:
            try:
                response = eks.describe_cluster(name=cluster_name)
                encryption_config = response.get('cluster', {}).get('encryptionConfig', [])
                
                is_secret_encrypted = False
                for config in encryption_config:
                    if 'secrets' in config.get('resources', []) and config.get('provider', {}).get('keyArn'):
                        is_secret_encrypted = True
                        break
                
                if not is_secret_encrypted:
                    unencrypted_clusters.append(cluster_name)

            except ClientError as e:
                print(f"[ERROR] 클러스터 '{cluster_name}' 정보 확인 중 오류: {e}")

        if not unencrypted_clusters:
            print("[✓ COMPLIANT] 4.15 모든 EKS 클러스터의 시크릿 암호화가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.15 시크릿 암호화가 비활성화된 EKS 클러스터가 존재합니다 ({len(unencrypted_clusters)}개).")
            print(f"  ├─ 해당 클러스터: {', '.join(unencrypted_clusters)}")
            print("  └─ 🔧 EKS 클러스터의 [구성] > [보안] 섹션에서 KMS 키를 이용한 시크릿 암호화를 활성화하세요.")

    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")