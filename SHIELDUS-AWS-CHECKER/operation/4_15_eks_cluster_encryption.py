#  4.operation/4_15_eks_cluster_encryption.py
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
    - 기존 클러스터에는 암호화 설정을 적용할 수 없음
    - 새 클러스터 생성 시 AWS 콘솔에서 encryptionConfig 포함하여 생성해야 함
    """
    if not unencrypted_clusters:
        print("[INFO] 조치할 클러스터가 없습니다.")
        return

    print("[FIX] 4.15 시크릿 암호화가 설정되지 않은 클러스터에 대한 수동 조치가 필요합니다.")
    print("      EKS는 클러스터 생성 시에만 시크릿 암호화를 설정할 수 있으므로 클러스터 재생성이 필요합니다")
    print("[GUIDE] 콘솔 기반 조치 방법:")
    print("  1. AWS Management Console → EKS → [클러스터 생성]")
    print("  2. '클러스터 이름, 버전, IAM 역할' 등 기본 정보 입력")
    print("  3. '시크릿 암호화' 항목에서 다음 설정 추가:")
    print("     - 암호화할 리소스: secrets")
    print("     - KMS 키: 기존 키 선택 또는 새 키 생성")
    print("  4. 나머지 설정 완료 후 클러스터 생성")
    print("  ※ 생성된 클러스터로 기존 리소스 마이그레이션 필요 (예: kubectl로 export/import)\n")

if __name__ == "__main__":
    clusters = check()
    fix(clusters)




# --------------------------------------------
# 암호화 설정하지 않고 eks cluster 생성하는 boto3 코드 (test 용)
# import boto3

# eks = boto3.client('eks')
# cluster_name = "unencrypted-cluster-test"

# response = eks.create_cluster(
#     name=cluster_name,
#     version='1.32',
#     roleArn='arn:aws:iam::040108639270:role/my-eks-cluster-eks-cluster-role',
#     resourcesVpcConfig={
#         'subnetIds': ['subnet-053cab1a41c4e43db', 'subnet-043f14a985134c6b9'],
#         'endpointPublicAccess': True
#     }
#     # 👇 encryptionConfig 생략!
#     # 'encryptionConfig': [ ... ] 없음!
# )

# print(f"[INFO] 클러스터 생성 요청 완료: {cluster_name}")