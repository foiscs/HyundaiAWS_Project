import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


# 4.operation/4_8_instance_logging.py
def check():
    """
    [4.8] 인스턴스 로깅 설정
    - EC2 인스턴스의 OS 및 애플리케이션 로그가 CloudWatch Logs로 전송되는지 점검 (수동 안내)
    """
    print("[INFO] 4.8 인스턴스 로깅 설정 체크 중...")
    print("[ⓘ MANUAL] EC2 인스턴스 내부의 로그 설정은 자동 점검이 불가능합니다.")
    print("  ├─ 점검 1: 인스턴스에 CloudWatch Agent가 설치 및 실행 중인지 확인하세요.")
    print("  ├─ 점검 2: CloudWatch Agent 구성 파일(/opt/aws/amazon-cloudwatch-agent/bin/config.json)에 OS 로그(예: /var/log/messages), 보안 로그(예: /var/log/secure), 애플리케이션 로그 파일이 정의되어 있는지 확인하세요.")
    print("  └─ 🔧 CloudWatch Agent를 설치하고 구성하여 중요한 인스턴스 로그를 CloudWatch Logs로 중앙 집중화하여 모니터링 및 분석하세요.")