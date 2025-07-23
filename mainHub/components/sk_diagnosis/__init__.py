"""
SK Shieldus 진단 모듈 - 진단 항목 팩토리
"""
from .account_management.user_account_1_1 import UserAccountChecker

# 진단 항목 레지스트리
DIAGNOSIS_REGISTRY = {
    "1.1": UserAccountChecker,
    # "1.2": IAMSingleAccountChecker,  # 향후 추가
    # "1.3": IAMIdentificationChecker,  # 향후 추가
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