import boto3
from botocore.exceptions import ClientError

def check():
    """
    [2.1] 인스턴스 서비스 정책 관리 (EC2, RDS, S3 등)
    - 주요 인스턴스 서비스에 대해 과도한 권한(*FullAccess)이 부여되었는지 점검하고, 해당 내역을 반환
    """
    print("[INFO] 2.1 인스턴스 서비스 정책 관리 체크 중...")
    iam = boto3.client('iam')
    overly_permissive_policies = {
        "arn:aws:iam::aws:policy/AmazonEC2FullAccess": "EC2",
        "arn:aws:iam::aws:policy/AmazonECS_FullAccess": "ECS",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess": "ECR",
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy": "EKS",
        "arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess": "EFS",
        "arn:aws:iam::aws:policy/AmazonRDSFullAccess": "RDS",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess": "S3"
    }
    findings = []

    try:
        for policy_arn, service_name in overly_permissive_policies.items():
            try:
                paginator = iam.get_paginator('list_entities_for_policy')
                for page in paginator.paginate(PolicyArn=policy_arn):
                    for user in page.get('PolicyUsers', []):
                        findings.append({'type': 'user', 'name': user['UserName'], 'policy': policy_arn.split('/')[-1]})
                    for group in page.get('PolicyGroups', []):
                        findings.append({'type': 'group', 'name': group['GroupName'], 'policy': policy_arn.split('/')[-1]})
                    for role in page.get('PolicyRoles', []):
                        findings.append({'type': 'role', 'name': role['RoleName'], 'policy': policy_arn.split('/')[-1]})
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity': continue
                else: raise e
        
        if not findings:
            print("[✓ COMPLIANT] 2.1 인스턴스 관련 서비스에 과도한 권한이 부여된 주체가 없습니다.")
        else:
            print(f"[⚠ WARNING] 2.1 인스턴스 관련 서비스에 과도한 권한이 부여되었습니다 ({len(findings)}건).")
            for f in findings: print(f"  ├─ {f['type'].capitalize()} '{f['name']}'에 '{f['policy']}' 정책 연결됨")
        
        return findings
    
    except ClientError as e:
        print(f"[ERROR] IAM 정책 정보를 가져오는 중 오류 발생: {e}")
        return []

def fix(findings):
    """
    [2.1] 인스턴스 서비스 정책 관리 조치
    - 권한 변경은 위험하므로 자동 조치 대신 수동 조치 가이드를 제공
    """
    if not findings:
        return

    print("[FIX] 2.1 과도한 권한 정책 조치는 운영에 큰 영향을 줄 수 있어 자동화되지 않습니다.")
    print("  └─ 아래 가이드에 따라 수동으로 조치하세요.")
    print("  └─ 1. [권장] AWS IAM Access Analyzer를 사용하여 실제 사용된 권한을 기반으로 세분화된 정책을 생성합니다.")
    print("  └─ 2. 생성된 새 정책을 해당 주체(사용자/그룹/역할)에 연결합니다.")
    print("  └─ 3. 충분한 테스트 후, 아래 명령어를 참고하여 기존의 과도한 정책을 분리합니다.")
    
    for f in findings:
        policy_arn = f"arn:aws:iam::aws:policy/{f['policy']}"
        if f['type'] == 'user':
            print(f"     aws iam detach-user-policy --user-name {f['name']} --policy-arn {policy_arn}")
        elif f['type'] == 'group':
            print(f"     aws iam detach-group-policy --group-name {f['name']} --policy-arn {policy_arn}")
        elif f['type'] == 'role':
            print(f"     aws iam detach-role-policy --role-name {f['name']} --policy-arn {policy_arn}")

if __name__ == "__main__":
    findings_list = check()
    fix(findings_list)