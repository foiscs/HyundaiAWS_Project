import boto3
from botocore.exceptions import ClientError

def check():
    """
    [4.15] EKS Cluster 암호화 설정
    - EKS 클러스터의 시크릿(Secret) 암호화가 활성화되어 있는지 점검
    """
    print("[INFO] 4.15 EKS Cluster 암호화 설정 체크 중...")
    eks = boto3.client('eks')
    
    try:
        clusters = eks.list_clusters().get('clusters', [])
        if not clusters:
            print("[INFO] 4.15 점검할 EKS 클러스터가 없습니다.")
            return []

        unencrypted_clusters = []
        for name in clusters:
            try:
                enc_config = eks.describe_cluster(name=name)['cluster'].get('encryptionConfig', [])
                if not any('secrets' in cfg.get('resources', []) for cfg in enc_config):
                    unencrypted_clusters.append(name)
            except ClientError as e:
                print(f"[ERROR] 클러스터 '{name}' 정보 확인 중 오류: {e}")

        if not unencrypted_clusters:
            print("[✓ COMPLIANT] 4.15 모든 EKS 클러스터의 시크릿 암호화가 활성화되어 있습니다.")
        else:
            print(f"[⚠ WARNING] 4.15 시크릿 암호화가 비활성화된 EKS 클러스터가 존재합니다 ({len(unencrypted_clusters)}개).")
            print(f"  ├─ 해당 클러스터: {', '.join(unencrypted_clusters)}")
        
        return unencrypted_clusters

    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록을 가져오는 중 오류 발생: {e}")
        return []

def fix(unencrypted_clusters):
    """
    [4.15] EKS Cluster 암호화 설정 조치
    - 기존 클러스터에 시크릿 암호화 활성화
    """
    if not unencrypted_clusters: return

    eks = boto3.client('eks')
    print("[FIX] 4.15 EKS 클러스터 시크릿 암호화 조치를 시작합니다.")
    key_arn = input("  -> 시크릿 암호화에 사용할 KMS Key ARN을 입력하세요: ").strip()
    if not key_arn:
        print("     [ERROR] KMS Key ARN은 필수입니다. 조치를 중단합니다.")
        return

    for name in unencrypted_clusters:
        if input(f"  -> 클러스터 '{name}'에 시크릿 암호화를 활성화하시겠습니까? (클러스터 업데이트가 진행됩니다) (y/n): ").lower() == 'y':
            try:
                eks.associate_encryption_config(
                    clusterName=name,
                    encryptionConfig=[{'resources': ['secrets'], 'provider': {'keyArn': key_arn}}]
                )
                print(f"     [SUCCESS] 클러스터 '{name}'의 시크릿 암호화 활성화 요청을 보냈습니다.")
            except ClientError as e:
                print(f"     [ERROR] 암호화 활성화 실패: {e}")

if __name__ == "__main__":
    clusters = check()
    fix(clusters)