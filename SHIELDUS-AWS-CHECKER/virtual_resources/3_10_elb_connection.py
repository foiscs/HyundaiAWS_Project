import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [3.10] ELB(Elastic Load Balancing) 연결 관리
    - ALB/NLB/GLB에 대해 주요 보안 설정을 점검 (HTTP 리스너, 로깅, 삭제 방지)
    """
    print("[INFO] 3.10 ELB 연결 관리 체크 중...")
    elbv2 = boto3.client('elbv2')
    findings = []
    
    try:
        response = elbv2.describe_load_balancers()
        if not response.get('LoadBalancers'):
            print("[INFO] 3.10 점검할 로드 밸런서(ALB/NLB/GLB)가 없습니다.")
            # Classic LB 점검은 생략 (필요 시 elb client로 추가)
            return

        for lb in response['LoadBalancers']:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']

            # 1. 로깅 점검
            attrs = elbv2.describe_load_balancer_attributes(LoadBalancerArn=lb_arn)['Attributes']
            logging_enabled = any(attr['Key'] == 'access_logs.s3.enabled' and attr['Value'] == 'true' for attr in attrs)
            if not logging_enabled:
                findings.append(f"LB '{lb_name}'에 액세스 로깅이 비활성화되어 있습니다.")

            # 2. 삭제 방지 점검
            deletion_protection = any(attr['Key'] == 'deletion_protection.enabled' and attr['Value'] == 'true' for attr in attrs)
            if not deletion_protection:
                findings.append(f"LB '{lb_name}'에 삭제 방지 기능이 비활성화되어 있습니다.")

            # 3. HTTP 리스너 점검
            listeners = elbv2.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']
            has_https = any(l['Protocol'] == 'HTTPS' for l in listeners)
            for listener in listeners:
                if listener['Protocol'] == 'HTTP':
                    # HTTP 리스너가 있는데 HTTPS 리스너가 없거나, 리디렉션 설정이 없는 경우
                    is_redirect = any(action.get('Type') == 'redirect' and action.get('RedirectConfig', {}).get('Protocol') == 'HTTPS' for action in listener.get('DefaultActions', []))
                    if not has_https:
                         findings.append(f"LB '{lb_name}'에 암호화되지 않은 HTTP 리스너만 존재합니다.")
                    elif not is_redirect:
                        findings.append(f"LB '{lb_name}'의 HTTP 리스너에 HTTPS 리디렉션이 설정되지 않았습니다.")
        
        if not findings:
            print("[✓ COMPLIANT] 3.10 모든 로드 밸런서가 주요 보안 설정을 충족합니다.")
        else:
            print(f"[⚠ WARNING] 3.10 로드 밸런서에 보안 설정이 미흡한 항목이 있습니다 ({len(findings)}건).")
            for finding in findings:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 로드 밸런서의 [속성 편집] 및 [리스너 편집]에서 액세스 로깅, 삭제 방지, HTTPS 리디렉션을 설정하세요.")

    except ClientError as e:
        print(f"[ERROR] 로드 밸런서 정보를 가져오는 중 오류 발생: {e}")