import boto3
import subprocess
from botocore.exceptions import ClientError

def _get_eks_clusters():
    """현재 리전의 모든 EKS 클러스터 이름을 가져옵니다."""
    try:
        eks = boto3.client('eks')
        clusters = eks.list_clusters()['clusters']
        return clusters
    except ClientError as e:
        print(f"[ERROR] EKS 클러스터 목록 조회 실패: {e}")
        return []

def _update_kubeconfig(cluster_name):
    """지정된 EKS 클러스터에 대한 kubeconfig를 업데이트합니다."""
    # 현재 AWS CLI에 설정된 리전을 사용
    region = boto3.session.Session().region_name
    command = ["aws", "eks", "update-kubeconfig", "--name", cluster_name, "--region", region]
    try:
        # kubeconfig 업데이트 결과를 숨기기 위해 stdout, stderr를 DEVNULL로 리디렉션
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        # 오류 발생 시에만 stderr 출력
        print(f"[ERROR] Kubeconfig 업데이트 실패 (클러스터: {cluster_name}): {e.stderr}")
        return False