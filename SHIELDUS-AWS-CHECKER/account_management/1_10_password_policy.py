import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager

def check():
    """
    [1.10] AWS 계정 패스워드 정책 관리
    - 계정의 패스워드 정책이 권장 기준을 충족하는지 점검
    - 기준: 최소 길이 8, 대/소문자, 숫자, 특수문자 중 3종류 이상 조합, 90일 이내 만료, 재사용 1회 이상 제한
    """
    print("[INFO] 1.10 AWS 계정 패스워드 정책 관리 체크 중...")
    iam = boto3.client('iam')
    findings = []

    try:
        response = iam.get_account_password_policy()
        policy = response['PasswordPolicy']
        
        if policy.get('MinimumPasswordLength', 0) < 8:
            findings.append(f"패스워드 최소 길이가 8 미만입니다 (현재: {policy.get('MinimumPasswordLength', '미설정')}).")
        
        complexity_count = sum([
            1 for key in ['RequireSymbols', 'RequireNumbers', 'RequireUppercaseCharacters', 'RequireLowercaseCharacters']
            if policy.get(key)
        ])
        if complexity_count < 3:
            findings.append(f"패스워드 복잡도(대/소/숫자/특수문자)가 3종류 미만으로 설정되었습니다 (현재: {complexity_count}종류).")
        
        if not policy.get('PasswordReusePrevention'):
            findings.append("패스워드 재사용 방지 정책이 설정되지 않았습니다.")
        
        if policy.get('ExpirePasswords', False):
            if policy.get('MaxPasswordAge', 1000) > 90:
                findings.append(f"패스워드 만료 기간이 90일을 초과합니다 (현재: {policy.get('MaxPasswordAge')}일).")
        else:
            findings.append("패스워드 만료 정책(ExpirePasswords)이 설정되지 않았습니다.")

        if not findings:
            print("[✓ COMPLIANT] 1.10 패스워드 정책이 권장 기준을 충족합니다.")
        else:
            print("[⚠ WARNING] 1.10 패스워드 정책이 권장 기준을 충족하지 않습니다.")
            for finding in findings:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 IAM 대시보드에서 계정 설정 > 암호 정책을 편집하여 보안을 강화하세요.")

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print("[⚠ WARNING] 1.10 계정에 패스워드 정책이 설정되어 있지 않습니다.")
            print("  └─ 🔧 IAM 대시보드에서 계정 설정 > 암호 정책을 설정하여 보안을 강화하세요.")
        else:
            print(f"[-] [ERROR] 패스워드 정책 정보를 가져오는 중 오류 발생: {e}")