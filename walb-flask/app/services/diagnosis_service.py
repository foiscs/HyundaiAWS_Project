"""
진단 서비스 - SK Shieldus 진단 엔진 및 비즈니스 로직
mainHub의 diagnosis_engine.py를 Flask용으로 이식
"""
import boto3 # type: ignore
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError # type: ignore
from app.config.diagnosis_config import DiagnosisConfig
from app.utils.aws_handler import AWSConnectionHandler
# 진단 로거 제거됨

class DiagnosisService:
    """진단 서비스 클래스 - mainHub의 DiagnosisCoreEngine 기능 이식"""
    
    def __init__(self):
        """진단 서비스 초기화"""
        self.config = DiagnosisConfig()
        self.aws_handler = AWSConnectionHandler()
        
    def get_sk_items(self):
        """SK Shieldus 41개 진단 항목 반환"""
        return self.config.get_sk_shieldus_items()
    
    def get_item_by_code(self, item_code):
        """항목 코드로 진단 항목 정보 반환"""
        return self.config.get_item_by_code(item_code)
    
    def create_aws_session(self, account):
        """
        AWS 세션 생성 (Role ARN 또는 Access Key 방식)
        
        Args:
            account: AWSAccount 모델 인스턴스
            
        Returns:
            boto3.Session or None: AWS 세션 객체
        """
        try:
            # 디버깅: 리전 정보 확인
            region = getattr(account, 'primary_region', 'ap-northeast-2') or 'ap-northeast-2'
            print(f"AWS 세션 생성 디버그: region={region}, connection_type={account.connection_type}")
            
            if account.connection_type == 'role':
                # Cross-Account Role 방식
                return self.aws_handler.create_session_from_role(
                    role_arn=account.role_arn,
                    external_id=account.external_id,
                    region=region
                )
            else:
                # Access Key 방식
                return self.aws_handler.create_session_from_keys(
                    access_key_id=account.access_key_id,
                    secret_access_key=account.secret_access_key,
                    region=region
                )
                
        except Exception as e:
            print(f"AWS 세션 생성 실패: {str(e)}")
            return None
    
    def test_aws_session(self, account):
        """
        AWS 세션 연결 테스트
        
        Args:
            account: AWSAccount 모델 인스턴스
            
        Returns:
            dict: 테스트 결과
        """
        try:
            if account.connection_type == 'role':
                # Cross-Account Role 테스트
                return self.aws_handler.test_cross_account_connection(
                    role_arn=account.role_arn,
                    external_id=account.external_id,
                    region=account.primary_region
                )
            else:
                # Access Key 테스트
                return self.aws_handler.test_access_key_connection(
                    access_key_id=account.access_key_id,
                    secret_access_key=account.secret_access_key,
                    region=account.primary_region
                )
                
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
    
    def run_single_diagnosis(self, account, item_code, enable_logging=True):
        """
        개별 진단 항목 실행
        
        Args:
            account: AWSAccount 모델 인스턴스
            item_code (str): 진단 항목 코드 (예: "1.1")
            enable_logging (bool): 로깅 활성화 여부
            
        Returns:
            dict: 진단 결과
        """
        try:
            # 진단 항목 정보 조회
            item_info = self.get_item_by_code(item_code)
            if not item_info:
                result = {
                    'status': 'error',
                    'message': f'진단 항목을 찾을 수 없습니다: {item_code}'
                }
                if enable_logging:
                    pass  # 로깅 제거됨
                return result
            
            # 진단 시작 로그
            if enable_logging:
                pass  # 로깅 제거됨
            
            # AWS 세션 생성
            aws_session = self.create_aws_session(account)
            if not aws_session:
                result = {
                    'status': 'error',
                    'message': 'AWS 세션 생성에 실패했습니다.'
                }
                if enable_logging:
                    pass  # 로깅 제거됨
                return result
            
            # 체커 인스턴스 생성 및 진단 실행
            checker = self._get_checker_instance(item_code, aws_session)
            if not checker:
                result = {
                    'status': 'error',
                    'message': f'진단 체커를 찾을 수 없습니다: {item_code}'
                }
                if enable_logging:
                    pass  # 로깅 제거됨
                return result
            
            # 진단 실행
            raw_result = checker.run_diagnosis()
            
            # 결과를 Flask 템플릿용으로 변환
            formatted_result = checker.get_result_summary(raw_result)
            
            # 결과 포맷팅
            result = {
                'status': 'success',
                'item_code': item_code,
                'item_name': item_info['name'],
                'category': item_info.get('category', ''),
                'severity': item_info['severity'],
                'result': formatted_result,
                'raw_result': raw_result,  # 원본 결과도 보관
                'executed_at': datetime.now().isoformat()
            }
            
            # 진단 결과 로그
            if enable_logging:
                pass  # 로깅 제거됨
            
            return result
            
        except Exception as e:
            result = {
                'status': 'error',
                'message': f'진단 실행 중 오류 발생: {str(e)}'
            }
            if enable_logging:
                item_name = item_info.get('name', '알 수 없는 항목') if 'item_info' in locals() else '알 수 없는 항목'

            return result
    
    def run_batch_diagnosis(self, account, item_codes=None, enable_logging=True):
        """
        일괄 진단 실행
        
        Args:
            account: AWSAccount 모델 인스턴스
            item_codes (list): 진단할 항목 코드 목록 (None이면 전체)
            enable_logging (bool): 로깅 활성화 여부
            
        Returns:
            dict: 일괄 진단 결과
        """
        session_id = None
        try:
            # 진단할 항목 결정
            if item_codes is None:
                # 전체 41개 항목 진단
                sk_items = self.get_sk_items()
                all_codes = []
                for category_items in sk_items.values():
                    for item in category_items:
                        all_codes.append(item['code'])
                item_codes = all_codes
            
            # 로깅 세션 시작
            if enable_logging:
                account_id = getattr(account, 'account_id', 'Unknown')
                account_name = getattr(account, 'cloud_name', None)
                pass  # 로깅 제거됨
            
            # AWS 세션 생성
            aws_session = self.create_aws_session(account)
            if not aws_session:
                result = {
                    'status': 'error',
                    'message': 'AWS 세션 생성에 실패했습니다.'
                }
                if enable_logging:
                    pass  # 로깅 제거됨
                return result
            
            # 각 항목별 진단 실행
            results = {}
            success_count = 0
            failed_count = 0
            
            for item_code in item_codes:
                result = self.run_single_diagnosis(account, item_code, enable_logging=enable_logging)
                results[item_code] = result
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
            
            # 세션 요약 로그
            log_file_path = None
            if enable_logging:
                pass  # 로깅 제거됨
            
            result = {
                'status': 'success',
                'total_items': len(item_codes),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results,
                'executed_at': datetime.now().isoformat()
            }
            
            # 로그 파일 경로 추가
            if enable_logging and log_file_path:
                result['log_file_path'] = log_file_path
                result['session_id'] = session_id
            
            return result
            
        except Exception as e:
            if enable_logging and session_id:
                pass  # 로깅 제거됨
            return {
                'status': 'error',
                'message': f'일괄 진단 실행 중 오류 발생: {str(e)}'
            }
    
    def execute_fix(self, account, item_code, selected_items):
        """
        자동 조치 실행
        
        Args:
            account: AWSAccount 모델 인스턴스
            item_code (str): 진단 항목 코드
            selected_items (dict): 조치할 항목들
            
        Returns:
            dict: 조치 실행 결과
        """
        try:
            # AWS 세션 생성
            aws_session = self.create_aws_session(account)
            if not aws_session:
                return {
                    'status': 'error',
                    'message': 'AWS 세션 생성에 실패했습니다.'
                }
            
            # 체커 인스턴스 생성
            checker = self._get_checker_instance(item_code, aws_session)
            if not checker:
                return {
                    'status': 'error',
                    'message': f'진단 체커를 찾을 수 없습니다: {item_code}'
                }
            
            # 조치 실행
            if hasattr(checker, 'execute_fix'):
                results = checker.execute_fix(selected_items)
                
                return {
                    'status': 'success',
                    'item_code': item_code,
                    'results': results,
                    'executed_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'해당 진단 항목은 자동 조치를 지원하지 않습니다: {item_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'조치 실행 중 오류 발생: {str(e)}'
            }
    
    def _get_checker_instance(self, item_code, aws_session):
        """
        진단 항목 코드로 체커 인스턴스 반환
        
        Args:
            item_code (str): 진단 항목 코드
            aws_session: AWS 세션 객체
            
        Returns:
            BaseChecker instance or None: 체커 인스턴스
        """
        try:
            # 체커 매핑 딕셔너리 (SHIELDUS-AWS-CHECKER에서 이식된 체커들)
            checker_mapping = {
                # 계정 관리 (13개) - 모두 구현 완료
                "1.1": "app.checkers.account_management.user_account_1_1.UserAccountChecker",
                "1.2": "app.checkers.account_management.iam_single_account_1_2.IAMSingleAccountChecker",
                "1.3": "app.checkers.account_management.iam_identification_1_3.IAMIdentificationChecker",
                "1.4": "app.checkers.account_management.iam_group_1_4.IAMGroupChecker",
                "1.5": "app.checkers.account_management.ec2_key_pair_access_1_5.KeyPairAccessChecker",
                "1.6": "app.checkers.account_management.s3_key_storage_1_6.S3KeyStorageChecker",
                "1.7": "app.checkers.account_management.root_account_usage_1_7.RootAccountUsageChecker",
                "1.8": "app.checkers.account_management.access_key_mgmt_1_8.AccessKeyManagementChecker",
                "1.9": "app.checkers.account_management.mfa_setting_1_9.MFASettingChecker",
                "1.10": "app.checkers.account_management.password_policy_1_10.PasswordPolicyChecker",
                "1.11": "app.checkers.account_management.eks_user_management_1_11.EKSUserManagementChecker",
                "1.12": "app.checkers.account_management.eks_service_account_1_12.EKSServiceAccountChecker",
                "1.13": "app.checkers.account_management.eks_anonymous_access_1_13.EKSAnonymousAccessChecker",
                
                # 권한 관리 (3개) - 모두 구현 완료
                "2.1": "app.checkers.authorization.instance_service_policy_2_1.InstanceServicePolicyChecker",
                "2.2": "app.checkers.authorization.network_service_policy_2_2.NetworkServicePolicyChecker",
                "2.3": "app.checkers.authorization.other_service_policy_2_3.OtherServicePolicyChecker",
                
                # 가상 자원 (10개) - 모두 구현 완료
                "3.1": "app.checkers.virtual_resources.sg_any_rule_3_1.SecurityGroupAnyRuleChecker",
                "3.2": "app.checkers.virtual_resources.sg_unnecessary_policy_3_2.SecurityGroupUnnecessaryPolicyChecker",
                "3.3": "app.checkers.virtual_resources.nacl_traffic_policy_3_3.NaclTrafficPolicyChecker",
                "3.4": "app.checkers.virtual_resources.route_table_policy_3_4.RouteTablePolicyChecker",
                "3.5": "app.checkers.virtual_resources.igw_connection_3_5.InternetGatewayConnectionChecker",
                "3.6": "app.checkers.virtual_resources.nat_gateway_connection_3_6.NatGatewayConnectionChecker",
                "3.7": "app.checkers.virtual_resources.s3_bucket_access_3_7.S3BucketAccessChecker",
                "3.8": "app.checkers.virtual_resources.rds_subnet_az_3_8.RdsSubnetAzChecker",
                "3.9": "app.checkers.virtual_resources.eks_pod_security_policy_3_9.EksPodSecurityPolicyChecker",
                "3.10": "app.checkers.virtual_resources.elb_connection_3_10.ElbConnectionChecker",
                
                # 운영 관리 (15개) - 모두 구현 완료
                "4.1": "app.checkers.operation.ebs_encryption_4_1.EbsEncryptionChecker",
                "4.2": "app.checkers.operation.rds_encryption_4_2.RdsEncryptionChecker",
                "4.3": "app.checkers.operation.s3_encryption_4_3.S3EncryptionChecker",
                "4.4": "app.checkers.operation.transit_encryption_4_4.TransitEncryptionChecker",
                "4.5": "app.checkers.operation.cloudtrail_encryption_4_5.CloudtrailEncryptionChecker",
                "4.6": "app.checkers.operation.cloudwatch_encryption_4_6.CloudwatchEncryptionChecker",
                "4.7": "app.checkers.operation.user_account_logging_4_7.UserAccountLoggingChecker",
                "4.8": "app.checkers.operation.instance_logging_4_8.InstanceLoggingChecker",
                "4.9": "app.checkers.operation.rds_logging_4_9.RdsLoggingChecker",
                "4.10": "app.checkers.operation.s3_bucket_logging_4_10.S3BucketLoggingChecker",
                "4.11": "app.checkers.operation.vpc_flow_logging_4_11.VpcFlowLoggingChecker",
                "4.12": "app.checkers.operation.log_retention_period_4_12.LogRetentionPeriodChecker",
                "4.13": "app.checkers.operation.backup_usage_4_13.BackupUsageChecker",
                "4.14": "app.checkers.operation.eks_control_plane_logging_4_14.EksControlPlaneLoggingChecker",
                "4.15": "app.checkers.operation.eks_cluster_encryption_4_15.EksClusterEncryptionChecker"
            }
            
            # 체커 클래스 경로 조회
            checker_path = checker_mapping.get(item_code)
            if not checker_path:
                print(f"체커 매핑을 찾을 수 없습니다: {item_code}")
                return None
            
            # 동적 임포트 및 인스턴스 생성
            module_path, class_name = checker_path.rsplit('.', 1)
            
            try:
                import importlib
                print(f"[DEBUG] 임포트 시도: {module_path}.{class_name}")
                module = importlib.import_module(module_path)
                print(f"[DEBUG] 모듈 임포트 성공: {module_path}")
                checker_class = getattr(module, class_name)
                print(f"[DEBUG] 클래스 조회 성공: {class_name}")
                return checker_class(session=aws_session)
            except ImportError as e:
                print(f"체커 모듈 임포트 실패 ({module_path}): {str(e)}")
                return None
            except AttributeError as e:
                print(f"체커 클래스를 찾을 수 없습니다 ({class_name}): {str(e)}")
                return None
                
        except Exception as e:
            print(f"체커 인스턴스 생성 실패 ({item_code}): {str(e)}")
            return None
    
    def get_diagnosis_stats(self):
        """진단 항목 통계 반환"""
        config = DiagnosisConfig()
        return {
            'total_items': config.get_total_items_count(),
            'severity_stats': config.get_severity_stats(),
            'category_stats': config.get_category_stats()
        }