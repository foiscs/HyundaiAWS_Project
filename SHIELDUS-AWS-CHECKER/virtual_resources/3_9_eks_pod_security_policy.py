import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.9] EKS Pod 보안 정책 관리
    - Pod Security Standards(PSS)가 네임스페이스에 적절히 적용되었는지 점검
    - PodSecurityPolicy(PSP)는 폐기되었으므로 PSS 기준으로 안내
    - Boto3만으로는 확인 불가. kubectl 명령어를 통해 확인하도록 안내
    """
    print("[INFO] 3.9 EKS Pod 보안 정책 관리 체크 중...")
    print("[ⓘ MANUAL] 이 항목은 Kubernetes API 접근이 필요하여 자동 점검이 제한됩니다.")
    print("  ├─ 네임스페이스에 Pod Security Standards(PSS) 레이블이 적절히 적용되었는지 수동으로 확인해야 합니다.")
    print("  ├─ 아래 명령어를 사용하여 네임스페이스의 보안 레이블을 확인하세요.")
    print("  └─ 🔧 명령어: kubectl get namespaces --show-labels")
    print("  └─ 🔧 점검사항: 'pod-security.kubernetes.io/enforce' 레이블이 'privileged'로 설정되었거나, 레이블 자체가 없는 네임스페이스가 있는지 확인하세요. 'baseline' 또는 'restricted' 사용을 권장합니다.")