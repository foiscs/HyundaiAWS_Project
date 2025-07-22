import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)




def check():
    """
    [1.11] EKS 사용자 관리
    - EKS Cluster의 'aws-auth' ConfigMap에 인가된 사용자만 접근하도록 설정되었는지 점검
    - Boto3만으로는 확인 불가. kubectl 명령어를 통해 확인하도록 안내
    """
    print("[INFO] 1.11 EKS 사용자 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes API 접근이 필요하여 자동 점검이 제한됩니다.")
    print(" ├─ EKS 클러스터의 'aws-auth' ConfigMap을 수동으로 확인해야 합니다.")
    print(" ├─ 아래 명령어를 사용하여 각 클러스터의 사용자 및 역할 매핑을 확인하세요.")
    print(" └─ 🔧 명령어: kubectl describe configmap aws-auth -n kube-system")
    print(" └─ 🔧 점검사항: 'mapUsers' 및 'mapRoles'에 불필요하거나 과도한 권한(예: system:masters)을 가진 항목이 없는지 확인하세요.")