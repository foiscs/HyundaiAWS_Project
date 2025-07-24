"""
SK Shieldus 진단 모듈 - 진단 항목 팩토리
"""
from .account_management.user_account_1_1 import UserAccountChecker
from .account_management.iam_single_account_1_2 import IAMSingleAccountChecker
from .account_management.iam_identification_1_3 import IAMIdentificationChecker
from .account_management.iam_group_1_4 import IAMGroupChecker
from .account_management.ec2_key_pair_access_1_5 import KeyPairAccessChecker
from .account_management.s3_key_pair_storage_1_6 import KeyPairStorageChecker
from .account_management.access_key_mgmt_1_8 import AccessKeyManagement18
from .account_management.mfa_setting_1_9 import MFASettingChecker
from .account_management.password_policy_1_10 import PasswordPolicyChecker
from .authorization.instance_service_policy_2_1 import InstanceServicePolicyChecker
from .authorization.network_service_policy_2_2 import NetworkServicePolicyChecker
from .authorization.other_service_policy_2_3 import OtherServicePolicyChecker

# 진단 항목 레지스트리
DIAGNOSIS_REGISTRY = {
    "1.1": UserAccountChecker,
    "1.2": IAMSingleAccountChecker,
    "1.3": IAMIdentificationChecker,
    "1.4": IAMGroupChecker,
    "1.5": KeyPairAccessChecker,
    "1.6": KeyPairStorageChecker,
    "1.8": AccessKeyManagement18,
    "1.9": MFASettingChecker,
    "1.10": PasswordPolicyChecker,
    "2.1": InstanceServicePolicyChecker,
    "2.2": NetworkServicePolicyChecker,
    "2.3": OtherServicePolicyChecker,
    # ... 다른 항목들
}

def get_checker(item_code):
    """진단 항목 코드로 체커 인스턴스 반환"""
    checker_class = DIAGNOSIS_REGISTRY.get(item_code)
    if checker_class:
        return checker_class()
    else:
        return None

def get_available_checkers():
    """사용 가능한 진단 항목 목록 반환"""
    return list(DIAGNOSIS_REGISTRY.keys())