"""
AWS 연결, 정책 생성, 검증 로직을 담당하는 핸들러
Flask 환경에 맞게 이식된 버전 (Streamlit 의존성 제거)

- AWSConnectionHandler: AWS 연결 및 권한 테스트 메인 클래스
- InputValidator: 입력값 검증 유틸리티 클래스
- simulate_connection_test: 개발/데모용 연결 테스트 시뮬레이션
"""
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app

class AWSConnectionHandler:
    """AWS 연결 및 권한 테스트를 담당하는 클래스"""
    
    def __init__(self):
        """
        핸들러 초기화
        - 테스트할 서비스 목록 정의
        """
        # WALB 서비스가 실행되는 EC2 인스턴스의 계정 ID
        self.walb_service_account_id = "253157413163"
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
    
    def generate_trust_policy(self, external_id, walb_account_id=None):
        """
        Trust Policy JSON 생성
        - Cross-Account Role의 신뢰 관계 정책
        - WALB 서비스가 Role을 Assume할 수 있도록 허용
        
        Args:
            external_id (str): 보안을 위한 External ID
            walb_account_id (str, optional): WALB 서비스 계정 ID (실제 환경에서 설정)
        """
        # 실제 WALB 서비스가 배포된 계정 ID 또는 기본값 사용
        account_id = walb_account_id or self.walb_service_account_id
        current_app.logger.info(f"Trust Policy - Account ID: '{account_id}'")
        
        # ARN 문자열을 EC2-KinesisForwarder-Role로 변경
        arn_string = f"arn:aws:iam::{account_id}:role/EC2-KinesisForwarder-Role"
        current_app.logger.info(f"Trust Policy - ARN: '{arn_string}'")
        
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": arn_string
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
        - mainHub와 동일하게 AdministratorAccess 권한 사용
        - SK Shieldus 41개 항목 완전 진단을 위한 전체 권한
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "*",
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
            # EC2 인스턴스 Role을 사용해서 STS 클라이언트 생성
            try:
                # EC2 인스턴스의 Role 자격증명을 자동으로 사용
                sts_client = boto3.client('sts', region_name=region)
                
                current_app.logger.info("EC2 인스턴스 Role로 STS 클라이언트 생성 성공")
                
            except Exception as e:
                return {
                    'status': 'failed',
                    'error_message': f'EC2 인스턴스 Role 설정 오류: {str(e)}'
                }
            
            current_app.logger.info(f"Role ARN으로 연결 시도: {role_arn}")
            current_app.logger.info(f"External ID: {external_id}")
                        
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName='walb-security-assessment',
                ExternalId=external_id,
                DurationSeconds=3600  # 1시간 (최대 12시간까지 가능)
            )
            
            # 임시 자격증명 추출
            credentials = response['Credentials']
            
            # 임시 자격증명으로 새 세션 생성
            assumed_session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            
            current_app.logger.info(f"Role Assumed 성공: {response['AssumedRoleUser']['Arn']}")
            
            # 각 서비스별 권한 테스트
            test_results = self._test_service_permissions(assumed_session)
            
            return {
                'status': 'success',
                'account_id': response['AssumedRoleUser']['Arn'].split(':')[4],
                'regions': self._count_available_regions(assumed_session),
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
            # 입력값 정리 (공백, 줄바꿈 제거)
            access_key_id = access_key_id.strip()
            secret_access_key = secret_access_key.strip()
            
            # 입력값 검증
            if not access_key_id or not secret_access_key:
                return {
                    'status': 'failed',
                    'error_message': 'Access Key ID 또는 Secret Access Key가 비어있습니다.'
                }
            
            current_app.logger.info(f"Access Key ID: {access_key_id}")
            current_app.logger.info(f"Secret Key 길이: {len(secret_access_key)}")
            
            # 세션 생성
            session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
            
            # STS로 계정 정보 확인
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            current_app.logger.info(f"연결된 계정 정보: {identity}")

            # ARN에서 사용자 ID 추출
            user_id = None
            arn = identity.get('Arn', '')
            if ':user/' in arn:
                # IAM 사용자의 경우: arn:aws:iam::123456789012:user/username
                user_id = arn.split(':user/')[-1]
            elif ':assumed-role/' in arn:
                # AssumeRole의 경우: arn:aws:sts::123456789012:assumed-role/role-name/session-name
                parts = arn.split(':assumed-role/')[-1].split('/')
                user_id = parts[0] if parts else None
            elif ':root' in arn:
                # Root 계정의 경우
                user_id = 'root'

            current_app.logger.info(f"추출된 사용자 ID: {user_id}")
                    
            # 각 서비스별 권한 테스트
            test_results = self._test_service_permissions(session)

            return {
                'status': 'success',
                'account_id': identity['Account'],
                'user_id': identity['UserId'],
                'user_arn': identity['Arn'],
                'regions': self._count_available_regions(session),
                'services': list(test_results.keys()),
                'permissions': test_results,
                'connection_time': datetime.now().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'SignatureDoesNotMatch':
                return {
                    'status': 'failed',
                    'error_code': error_code,
                    'error_message': '🔑 AWS 자격증명 오류: Secret Access Key를 다시 확인해주세요.\n'
                                '• 복사 시 공백이나 줄바꿈이 포함되지 않았는지 확인\n'
                                '• 키가 올바른지 AWS 콘솔에서 재확인\n'
                                '• 새로운 Access Key를 생성해보세요'
                }
            elif error_code == 'InvalidUserID.NotFound':
                return {
                    'status': 'failed',
                    'error_code': error_code,
                    'error_message': '🔍 Access Key ID가 존재하지 않습니다. AWS 콘솔에서 확인해주세요.'
                }
            else:
                return {
                    'status': 'failed',
                    'error_code': error_code,
                    'error_message': f'AWS API 오류: {error_message}'
                }
        except NoCredentialsError:
            return {
                'status': 'failed',
                'error_message': '🔐 AWS 자격증명이 제공되지 않았습니다.'
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
            cloudwatch.list_metrics()
            results['CloudWatch'] = True
        except Exception as e:
            current_app.logger.warning(f"CloudWatch 테스트 실패: {str(e)}")
            results['CloudWatch'] = False
        
        # RDS 권한 테스트
        try:
            rds = session.client('rds')
            rds.describe_db_instances(MaxRecords=20)
            results['RDS'] = True
        except Exception as e:
            current_app.logger.warning(f"RDS 테스트 실패: {str(e)}")
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
        
    def create_session_from_role(self, role_arn, external_id, region='ap-northeast-2'):
        """Cross-Account Role로 세션 생성 (EC2 인스턴스 Role 사용)"""
        try:
            # EC2 인스턴스의 Role 자격증명을 자동으로 사용
            sts_client = boto3.client('sts', region_name=region)
            print(f"AssumeRole 시도: role_arn={role_arn}, external_id={external_id}")
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName='walb-diagnosis-session',
                ExternalId=external_id,
                DurationSeconds=3600
            )
            print(f"AssumeRole 성공: {response['AssumedRoleUser']['Arn']}")
            
            credentials = response['Credentials']
            return boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
        except Exception as e:
            raise Exception(f"Role 세션 생성 실패: {str(e)}")

    def create_session_from_keys(self, access_key_id, secret_access_key, region='ap-northeast-2'):
        """Access Key로 세션 생성"""
        try:
            return boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
        except Exception as e:
            raise Exception(f"Key 세션 생성 실패: {str(e)}")

    def extract_account_id_from_role_arn(self, role_arn):
        """Role ARN에서 계정 ID 추출"""
        try:
            # arn:aws:iam::123456789012:role/RoleName 형식에서 계정 ID 추출
            parts = role_arn.split(':')
            if len(parts) >= 5 and parts[0] == 'arn' and parts[1] == 'aws' and parts[2] == 'iam':
                return parts[4]
            return None
        except:
            return None
    
class InputValidator:
    """입력값 검증을 담당하는 클래스"""
    
    @staticmethod
    def validate_account_id(account_id):
        """
        AWS 계정 ID 형식 검증
        - 12자리 숫자인지 확인
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
        """Role ARN 형식 검증"""
        if not role_arn:
            return False, "Role ARN을 입력하세요."
        
        if not role_arn.startswith('arn:aws:iam::'):
            return False, "올바른 Role ARN 형식이 아닙니다."
        
        if ':role/' not in role_arn:
            return False, "Role ARN에 ':role/'이 포함되어야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_access_key(access_key_id):
        """Access Key ID 형식 검증"""
        if not access_key_id:
            return False, "Access Key ID를 입력하세요."
        
        if not access_key_id.startswith('AKIA'):
            return False, "Access Key ID는 'AKIA'로 시작해야 합니다."
        
        if len(access_key_id) != 20:
            return False, "Access Key ID는 20자리여야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_secret_key(secret_key):
        """Secret Access Key 형식 검증"""
        if not secret_key:
            return False, "Secret Access Key를 입력하세요."
        
        if len(secret_key) != 40:
            return False, "Secret Access Key는 40자리여야 합니다."
        
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """이메일 형식 검증"""
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