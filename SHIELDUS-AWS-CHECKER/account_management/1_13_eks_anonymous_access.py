import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [1.13] EKS 불필요한 익명 접근 관리
    - 'system:anonymous' 나 'system:unauthenticated' 그룹에 불필요한 권한이 바인딩되지 않았는지 점검
    - Boto3만으로는 확인 불가. kubectl 명령어를 통해 확인하도록 안내
    """
    print("[INFO] 1.13 EKS 불필요한 익명 접근 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes API 접근이 필요하여 자동 점검이 제한됩니다.")
    print(" ├─ 익명 사용자에 대한 RoleBinding/ClusterRoleBinding을 수동으로 확인해야 합니다.")
    print(" ├─ 아래 명령어를 사용하여 'system:anonymous' 또는 'system:unauthenticated'에 대한 바인딩을 확인하세요.")
    print(" └─ 🔧 명령어 (ClusterRoleBinding): kubectl get clusterrolebindings -o jsonpath='{.items[?(@.subjects[0].name==\"system:anonymous\")]}'")
    print(" └─ 🔧 명령어 (RoleBinding): kubectl get rolebindings --all-namespaces -o jsonpath='{.items[?(@.subjects[0].name==\"system:anonymous\")]}'")
    print(" └─ 🔧 점검사항: 'system:public-info-viewer' 외의 불필요한 권한이 익명 사용자에게 부여되지 않았는지 확인하고, 있다면 제거하세요.")
