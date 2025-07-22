import boto3
from botocore.exceptions import ClientError
import os, sys

# 상위 디렉토리 경로 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from aws_client import AWSClientManager


import boto3
from botocore.exceptions import ClientError

def check():
    """
    [2.1] 인스턴스 서비스 정책 관리 (EC2, ECS, ECR, EKS, EFS, RDS, S3)
    - 주요 인스턴스 서비스에 대해 과도한 권한(예: *FullAccess)이 부여되었는지 점검
    """
    print("[INFO] 2.1 인스턴스 서비스 정책 관리 체크 중...")
    iam = boto3.client('iam')
    overly_permissive_policies = {
        "arn:aws:iam::aws:policy/AmazonEC2FullAccess": "EC2",
        "arn:aws:iam::aws:policy/AmazonECS_FullAccess": "ECS",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess": "ECR",
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy": "EKS", # EKS는 FullAccess가 일반적이므로 ClusterPolicy 점검
        "arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess": "EFS",
        "arn:aws:iam::aws:policy/AmazonRDSFullAccess": "RDS",
        "arn:aws:iam::aws:policy/AmazonS3FullAccess": "S3"
    }
    findings = []

    try:
        for policy_arn, service_name in overly_permissive_policies.items():
            paginator = iam.get_paginator('list_entities_for_policy')
            try:
                for page in paginator.paginate(PolicyArn=policy_arn):
                    for user in page.get('PolicyUsers', []):
                        findings.append(f"사용자 '{user['UserName']}'에 과도한 {service_name} 권한 정책('{policy_arn.split('/')[-1]}')이 연결됨")
                    for role in page.get('PolicyRoles', []):
                        # EC2 인스턴스 프로파일 역할에 과도한 권한이 있는지 집중 점검
                        if ":instance-profile/" in role['Arn'] or "ec2.amazonaws.com" in str(role.get('AssumeRolePolicyDocument')):
                             findings.append(f"역할 '{role['RoleName']}'에 과도한 {service_name} 권한 정책('{policy_arn.split('/')[-1]}')이 연결됨")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    continue # 정책이 존재하지 않으면 점검 스킵
                else:
                    raise e
        
        if not findings:
            print("[✓ COMPLIANT] 2.1 인스턴스 관련 서비스에 과도한 권한(FullAccess)이 부여된 주체(사용자/역할)가 없습니다.")
        else:
            print(f"[⚠ WARNING] 2.1 인스턴스 관련 서비스에 과도한 권한이 부여되었습니다 ({len(findings)}건).")
            for finding in findings:
                print(f"  ├─ {finding}")
            print("  └─ 🔧 최소 권한 원칙(Least Privilege)에 따라 필요한 작업만 허용하는 맞춤형 정책을 생성하여 적용하세요.")
    
    except ClientError as e:
        print(f"[-] [ERROR] IAM 정책 정보를 가져오는 중 오류 발생: {e}")