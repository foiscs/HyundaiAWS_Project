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
    [1.12] EKS 서비스 어카운트 관리
    - Pod에서 Kubernetes API 호출이 필요 없는 경우, 서비스 어카운트 토큰 자동 마운트를 비활성화했는지 점검
    - Boto3만으로는 확인 불가. kubectl 명령어를 통해 확인하도록 안내
    """
    print("[INFO] 1.12 EKS 서비스 어카운트 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes API 접근이 필요하여 자동 점검이 제한됩니다.")
    print("  ├─ Kubernetes API 접근이 필요 없는 Pod/ServiceAccount의 'automountServiceAccountToken' 설정을 확인해야 합니다.")
    print("  ├─ 확인 방법 1: Pod Spec 확인")
    print("  │ └─ `spec.automountServiceAccountToken: false` 설정 여부 확인")
    print("  ├─ 확인 방법 2: ServiceAccount 확인")
    print("  │ └─ `automountServiceAccountToken: false` 설정 여부 확인")
    print("  └─ 🔧 명령어 (기본 SA 확인): kubectl get serviceaccount default -n <네임스페이스> -o yaml")
    print("  └─ 🔧 점검사항: API 접근이 불필요한 애플리케이션에 토큰이 자동으로 마운트되지 않도록 위 설정을 적용하세요.")