"""
AWS 연결, 정책 생성, 검증 로직을 담당하는 핸들러
boto3를 이용한 실제 AWS API 호출 및 권한 테스트

- AWSConnectionHandler: AWS 연결 및 권한 테스트 메인 클래스
  - generate_external_id: 보안용 External ID 생성
  - generate_trust_policy: Cross-Account Role 신뢰 관계 정책 생성
  - generate_permission_policy: 보안 진단용 권한 정책 생성
  - test_cross_account_connection: Role을 통한 연결 테스트
  - test_access_key_connection: Access Key를 통한 연결 테스트
  - _test_service_permissions: 7개 AWS 서비스별 권한 확인
  - _count_available_regions: 접근 가능한 리전 수 계산
- InputValidator: 입력값 검증 유틸리티 클래스
  - validate_account_id: 12자리 AWS 계정 ID 형식 검증
  - validate_role_arn: IAM Role ARN 형식 검증
  - validate_access_key: Access Key ID 형식 검증
  - validate_secret_key: Secret Access Key 형식 검증
  - validate_email: 이메일 주소 형식 검증
- simulate_connection_test: 개발/데모용 연결 테스트 시뮬레이션
"""

import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

class AWSConnectionHandler:
    """AWS 연결 및 권한 테스트를 담당하는 클래스"""
    
    def __init__(self):
        """
        핸들러 초기화
        - WALB 메인 계정 정보 설정
        - 테스트할 서비스 목록 정의
        """
        self.walb_account_id = "999999999999"  # WALB 메인 계정 ID
        self.test_services = [
            'ec2', 's3', 'iam', 'cloudtrail', 
            'cloudwatch', 'rds', 'eks'
        ]
    
    def generate_external_id(self):
        """
        External ID 생성
        - Cross-Account Role에서 사용할 고유 식별자
        - 보안을 위해 현재 시간 기반으로 생성
        
        Returns:
            str: walb-{timestamp} 형식의 External ID
        """
        timestamp = int(datetime.now().timestamp())
        return f"walb-{timestamp}"
    
    def generate_trust_policy(self, external_id):
        """
        Trust Policy JSON 생성
        - Cross-Account Role의 신뢰 관계 정책
        - WALB 계정이 Role을 Assume할 수 있도록 허용
        
        Args:
            external_id (str): 보안을 위한 External ID
            
        Returns:
            dict: Trust Policy JSON 객체
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{self.walb_account_id}:root"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "sts:ExternalId": external_id
                        }
                    }
                }
            ]
        }
    
    def generate_permission_policy(self):
        """
        Permission Policy JSON 생성
        - Role에 부여할 실제 권한 정책
        - 보안 진단에 필요한 읽기 권한만 부여
        
        Returns:
            dict: Permission Policy JSON 객체
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        # EC2 관련 읽기 권한
                        "ec2:Describe*",
                        
                        # S3 관련 읽기 권한
                        "s3:GetBucket*",
                        "s3:ListBucket*",
                        "s3:GetObject*",
                        
                        # IAM 관련 읽기 권한
                        "iam:List*",
                        "iam:Get*",
                        
                        # CloudTrail 관련 읽기 권한
                        "cloudtrail:Describe*",
                        "cloudtrail:Get*",
                        "cloudtrail:List*",
                        
                        # CloudWatch 관련 읽기 권한
                        "cloudwatch:Get*",
                        "cloudwatch:List*",
                        "cloudwatch:Describe*",
                        "logs:Describe*",
                        "logs:Get*",
                        
                        # RDS 관련 읽기 권한
                        "rds:Describe*",
                        
                        # EKS 관련 읽기 권한
                        "eks:Describe*",
                        "eks:List*"
                    ],
                    "Resource": "*"
                }
            ]
        }
    
    def test_cross_account_connection(self, role_arn, external_id, region='ap-northeast-2'):
        """
        Cross-Account Role을 이용한 연결 테스트
        - STS AssumeRole을 통해 임시 자격증명 획득
        - 각 서비스별 권한 테스트 수행
        
        Args:
            role_arn (str): 테스트할 Role의 ARN
            external_id (str): Role에 설정된 External ID
            region (str): 기본 리전 (기본값: ap-northeast-2)
            
        Returns:
            dict: 연결 테스트 결과
        """
        try:
            # STS 클라이언트로 Role Assume 시도
            sts_client = boto3.client('sts', region_name=region)
            
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName='walb-security-assessment',
                ExternalId=external_id
            )
            
            # 임시 자격증명 추출
            credentials = response['Credentials']
            
            # 임시 자격증명으로 새 세션 생성
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            
            # 각 서비스별 권한 테스트
            test_results = self._test_service_permissions(session)
            
            return {
                'status': 'success',
                'account_id': response['AssumedRoleUser']['Arn'].split(':')[4],
                'regions': self._count_available_regions(session),
                'services': list(test_results.keys()),
                'permissions': test_results,
                'connection_time': datetime.now().isoformat()
            }
            
        except ClientError as e:
            return {
                'status': 'failed',
                'error_code': e.response['Error']['Code'],
                'error_message': e.response['Error']['Message']
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
    
    def test_access_key_connection(self, access_key_id, secret_access_key, region='ap-northeast-2'):
        """
        Access Key를 이용한 연결 테스트
        - 직접 자격증명을 이용한 AWS API 호출
        - 각 서비스별 권한 테스트 수행
        
        Args:
            access_key_id (str): AWS Access Key ID
            secret_access_key (str): AWS Secret Access Key
            region (str): 기본 리전 (기본값: ap-northeast-2)
            
        Returns:
            dict: 연결 테스트 결과
        """
        try:
            # 세션 생성
            session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
            
            # STS로 계정 정보 확인
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            
            # 각 서비스별 권한 테스트
            test_results = self._test_service_permissions(session)
            
            return {
                'status': 'success',
                'account_id': identity['Account'],
                'user_arn': identity['Arn'],
                'regions': self._count_available_regions(session),
                'services': list(test_results.keys()),
                'permissions': test_results,
                'connection_time': datetime.now().isoformat()
            }
            
        except (ClientError, NoCredentialsError) as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
    
    def _test_service_permissions(self, session):
        """
        각 AWS 서비스별 권한 테스트 수행
        - 실제 API 호출을 통해 권한 확인
        - 에러 발생 시 권한 없음으로 판단
        
        Args:
            session (boto3.Session): 테스트할 AWS 세션
            
        Returns:
            dict: 서비스별 권한 테스트 결과 (True/False)
        """
        results = {}
        
        # EC2 권한 테스트
        try:
            ec2 = session.client('ec2')
            ec2.describe_instances(MaxResults=5)
            results['EC2'] = True
        except:
            results['EC2'] = False
        
        # S3 권한 테스트
        try:
            s3 = session.client('s3')
            s3.list_buckets()
            results['S3'] = True
        except:
            results['S3'] = False
        
        # IAM 권한 테스트
        try:
            iam = session.client('iam')
            iam.list_users(MaxItems=5)
            results['IAM'] = True
        except:
            results['IAM'] = False
        
        # CloudTrail 권한 테스트
        try:
            cloudtrail = session.client('cloudtrail')
            cloudtrail.describe_trails()
            results['CloudTrail'] = True
        except:
            results['CloudTrail'] = False
        
        # CloudWatch 권한 테스트
        try:
            cloudwatch = session.client('cloudwatch')
            cloudwatch.list_metrics(MaxRecords=5)
            results['CloudWatch'] = True
        except:
            results['CloudWatch'] = False
        
        # RDS 권한 테스트
        try:
            rds = session.client('rds')
            rds.describe_db_instances(MaxRecords=5)
            results['RDS'] = True
        except:
            results['RDS'] = False
        
        # EKS 권한 테스트
        try:
            eks = session.client('eks')
            eks.list_clusters(maxResults=5)
            results['EKS'] = True
        except:
            results['EKS'] = False
        
        return results
    
    def _count_available_regions(self, session):
        """
        접근 가능한 리전 수 계산
        - EC2 서비스를 통해 활성화된 리전 수 확인
        
        Args:
            session (boto3.Session): AWS 세션
            
        Returns:
            int: 접근 가능한 리전 수
        """
        try:
            ec2 = session.client('ec2')
            regions = ec2.describe_regions()
            return len(regions['Regions'])
        except:
            return 0

class InputValidator:
    """입력값 검증을 담당하는 클래스"""
    
    @staticmethod
    def validate_account_id(account_id):
        """
        AWS 계정 ID 형식 검증
        - 12자리 숫자인지 확인
        
        Args:
            account_id (str): 검증할 계정 ID
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not account_id:
            return False, "계정 ID를 입력하세요."
        
        if not account_id.isdigit():
            return False, "계정 ID는 숫자만 포함해야 합니다."
        
        if len(account_id) != 12:
            return False, "계정 ID는 12자리여야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_role_arn(role_arn):
        """
        Role ARN 형식 검증
        - AWS IAM Role ARN 형식 확인
        
        Args:
            role_arn (str): 검증할 Role ARN
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not role_arn:
            return False, "Role ARN을 입력하세요."
        
        if not role_arn.startswith('arn:aws:iam::'):
            return False, "올바른 Role ARN 형식이 아닙니다."
        
        if ':role/' not in role_arn:
            return False, "Role ARN에 ':role/'이 포함되어야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_access_key(access_key_id):
        """
        Access Key ID 형식 검증
        - AWS Access Key ID 형식 확인
        
        Args:
            access_key_id (str): 검증할 Access Key ID
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not access_key_id:
            return False, "Access Key ID를 입력하세요."
        
        if not access_key_id.startswith('AKIA'):
            return False, "Access Key ID는 'AKIA'로 시작해야 합니다."
        
        if len(access_key_id) != 20:
            return False, "Access Key ID는 20자리여야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_secret_key(secret_key):
        """
        Secret Access Key 형식 검증
        - 기본적인 길이 및 형식 확인
        
        Args:
            secret_key (str): 검증할 Secret Access Key
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not secret_key:
            return False, "Secret Access Key를 입력하세요."
        
        if len(secret_key) != 40:
            return False, "Secret Access Key는 40자리여야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """
        이메일 형식 검증
        - 기본적인 이메일 형식 확인
        
        Args:
            email (str): 검증할 이메일 주소
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email:
            return True, ""  # 이메일은 선택사항
        
        if '@' not in email or '.' not in email:
            return False, "올바른 이메일 형식이 아닙니다."
        
        return True, ""

def simulate_connection_test():
    """
    연결 테스트 시뮬레이션
    - 실제 AWS 호출 없이 테스트 결과 시뮬레이션
    - 개발/데모 환경에서 사용
    
    Returns:
        dict: 모의 테스트 결과
    """
    # 3초 대기 (실제 API 호출 시뮬레이션)
    time.sleep(3)
    
    return {
        'status': 'success',
        'account_id': '123456789012',
        'regions': 16,
        'services': ['EC2', 'S3', 'IAM', 'CloudTrail', 'CloudWatch', 'RDS', 'EKS'],
        'permissions': {
            'EC2': True,
            'S3': True,
            'IAM': True,
            'CloudTrail': True,
            'CloudWatch': True,
            'RDS': False,  # 일부 권한 없음 시뮬레이션
            'EKS': False
        },
        'connection_time': datetime.now().isoformat()
    }