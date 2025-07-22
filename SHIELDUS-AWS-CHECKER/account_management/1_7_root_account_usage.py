import boto3
from botocore.exceptions import ClientError

def check():
    """
    [1.7] Admin Console(Root) 관리자 정책 관리
    - Root 계정에 Access Key가 생성되어 있는지 점검하고, 존재 여부를 반환
    """
    print("[INFO] 1.7 Admin Console(Root) 관리자 정책 관리 체크 중...")
    iam = boto3.client('iam')
    root_key_exists = False
    
    try:
        summary = iam.get_account_summary()
        if summary['SummaryMap']['AccountAccessKeysPresent'] == 1:
            root_key_exists = True
            print("[⚠ WARNING] 1.7 Root 계정에 Access Key가 존재합니다.")
            print("  └─ Root 계정의 Access Key는 일상적인 작업에 사용해서는 안 됩니다.")
        else:
            print("[✓ COMPLIANT] 1.7 Root 계정에 Access Key가 생성되어 있지 않습니다.")
        
        return root_key_exists
    
    except ClientError as e:
        print(f"[ERROR] 계정 요약 정보를 가져오는 중 오류 발생: {e}")
        return False

def fix(root_key_exists):
    """
    [1.7] Admin Console(Root) 관리자 정책 관리 조치
    - Root Access Key 삭제는 매우 위험하므로 수동 조치 안내
    """
    if not root_key_exists:
        return

    print("[FIX] 1.7 Root 계정 Access Key 삭제는 매우 위험하므로 자동화되지 않습니다.")
    print("  └─ 이 키가 현재 사용 중인지 반드시 확인한 후, AWS Management Console에 Root 계정으로 직접 로그인하여 삭제하세요.")
    print("  └─ [내 보안 자격 증명] > [액세스 키] 섹션에서 키를 비활성화하고 삭제할 수 있습니다.")

if __name__ == "__main__":
    key_exists = check()
    fix(key_exists)