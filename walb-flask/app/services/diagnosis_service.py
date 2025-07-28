"""
진단 서비스 - SK Shieldus 진단 엔진 및 비즈니스 로직
mainHub의 diagnosis_engine.py를 Flask용으로 이식
"""
import boto3
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from app.config.diagnosis_config import DiagnosisConfig
from app.utils.aws_handler import AWSConnectionHandler

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
            if account.connection_type == 'cross-account-role':
                # Cross-Account Role 방식
                return self.aws_handler.create_session_from_role(
                    role_arn=account.role_arn,
                    external_id=account.external_id,
                    region=account.primary_region
                )
            else:
                # Access Key 방식
                return self.aws_handler.create_session_from_keys(
                    access_key_id=account.access_key_id,
                    secret_access_key=account.secret_access_key,
                    region=account.primary_region
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
            if account.connection_type == 'cross-account-role':
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
    
    def run_single_diagnosis(self, account, item_code):
        """
        개별 진단 항목 실행
        
        Args:
            account: AWSAccount 모델 인스턴스
            item_code (str): 진단 항목 코드 (예: "1.1")
            
        Returns:
            dict: 진단 결과
        """
        try:
            # 진단 항목 정보 조회
            item_info = self.get_item_by_code(item_code)
            if not item_info:
                return {
                    'status': 'error',
                    'message': f'진단 항목을 찾을 수 없습니다: {item_code}'
                }
            
            # AWS 세션 생성
            aws_session = self.create_aws_session(account)
            if not aws_session:
                return {
                    'status': 'error',
                    'message': 'AWS 세션 생성에 실패했습니다.'
                }
            
            # 체커 인스턴스 생성 및 진단 실행
            checker = self._get_checker_instance(item_code, aws_session)
            if not checker:
                return {
                    'status': 'error',
                    'message': f'진단 체커를 찾을 수 없습니다: {item_code}'
                }
            
            # 진단 실행
            raw_result = checker.run_diagnosis()
            
            # 결과를 Flask 템플릿용으로 변환
            formatted_result = checker.get_result_summary(raw_result)
            
            # 결과 포맷팅
            return {
                'status': 'success',
                'item_code': item_code,
                'item_name': item_info['name'],
                'category': item_info.get('category', ''),
                'severity': item_info['severity'],
                'result': formatted_result,
                'raw_result': raw_result,  # 원본 결과도 보관
                'executed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'진단 실행 중 오류 발생: {str(e)}'
            }
    
    def run_batch_diagnosis(self, account, item_codes=None):
        """
        일괄 진단 실행
        
        Args:
            account: AWSAccount 모델 인스턴스
            item_codes (list): 진단할 항목 코드 목록 (None이면 전체)
            
        Returns:
            dict: 일괄 진단 결과
        """
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
            
            # AWS 세션 생성
            aws_session = self.create_aws_session(account)
            if not aws_session:
                return {
                    'status': 'error',
                    'message': 'AWS 세션 생성에 실패했습니다.'
                }
            
            # 각 항목별 진단 실행
            results = {}
            success_count = 0
            failed_count = 0
            
            for item_code in item_codes:
                result = self.run_single_diagnosis(account, item_code)
                results[item_code] = result
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                'status': 'success',
                'total_items': len(item_codes),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results,
                'executed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
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
                
                # 가상 자원 (2개)
                "3.1": "app.checkers.virtual_resources.security_group_any_3_1.SecurityGroupAnyChecker",  # 구현 필요
                "3.2": "app.checkers.virtual_resources.security_group_unnecessary_3_2.SecurityGroupUnnecessaryChecker"  # 구현 필요
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