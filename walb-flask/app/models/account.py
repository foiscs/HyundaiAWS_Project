"""
AWS 계정 모델 - JSON 기반 데이터 관리
mainHub 구조와 호환되는 계정 데이터 관리
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from flask import current_app

class AWSAccount:
    def __init__(self, data: Dict):
        # mainHub와 호환되는 필드명 사용
        self.account_id = data.get('account_id', '')
        self.cloud_name = data.get('cloud_name', '')
        self.primary_region = data.get('primary_region', 'ap-northeast-2')
        self.contact_email = data.get('contact_email', '')
        
        # Role 기반 연결
        self.role_arn = data.get('role_arn', '')
        self.external_id = data.get('external_id', '')
        
        # Access Key 기반 연결 (mainHub 필드명과 동일)
        self.access_key_id = data.get('access_key_id', data.get('access_key', ''))
        self.secret_access_key = data.get('secret_access_key', data.get('secret_key', ''))
        
        # 연결 타입 자동 결정
        self.connection_type = self._determine_connection_type()
        
        # 메타데이터
        self.created_at = data.get('created_at', datetime.now().isoformat())
        self.status = data.get('status', 'active')
    
    def _determine_connection_type(self):
        """연결 타입 자동 결정"""
        if self.role_arn:
            return 'role'
        elif self.access_key_id:
            return 'access_key'
        else:
            return 'unknown'
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환 (mainHub 호환 형식)"""
        return {
            'account_id': self.account_id,
            'cloud_name': self.cloud_name,
            'primary_region': self.primary_region,
            'contact_email': self.contact_email,
            'role_arn': self.role_arn,
            'external_id': self.external_id,
            'access_key_id': self.access_key_id,
            'secret_access_key': self.secret_access_key,
            'connection_type': self.connection_type,
            'status': self.status,
            'created_at': self.created_at
        }
    
    @property
    def is_role_based(self) -> bool:
        """Role 기반 연결인지 확인"""
        return bool(self.role_arn)
    
    @property
    def is_access_key_based(self) -> bool:
        """Access Key 기반 연결인지 확인"""
        return bool(self.access_key_id)
    
    @property
    def connection_display_name(self) -> str:
        """연결 방식 표시명"""
        if self.is_role_based:
            return "🛡️ Cross-Account Role"
        elif self.is_access_key_based:
            return "🔑 Access Key"
        else:
            return "❓ 알 수 없음"
    
    def get_masked_credentials(self) -> Dict:
        """민감정보 마스킹된 자격증명 반환"""
        result = {}
        
        if self.is_role_based:
            result['role_arn'] = self.role_arn
            result['external_id'] = self.external_id
        elif self.is_access_key_based:
            # Access Key ID는 앞 4자리만 표시
            if self.access_key_id:
                result['access_key_id'] = self.access_key_id[:4] + "*" * 16
            # Secret Key는 완전히 마스킹
            if self.secret_access_key:
                result['secret_access_key'] = "*" * 40
        
        return result
    
    def validate(self) -> tuple[bool, str]:
        """계정 데이터 유효성 검사"""
        if not self.account_id:
            return False, "계정 ID가 필요합니다"
        
        if not self.cloud_name:
            return False, "클라우드 이름이 필요합니다"
        
        if not self.account_id.isdigit() or len(self.account_id) != 12:
            return False, "계정 ID는 12자리 숫자여야 합니다"
        
        # 연결 방식별 검증
        if self.connection_type == 'role':
            if not self.role_arn:
                return False, "Role ARN이 필요합니다"
            if not self.role_arn.startswith('arn:aws:iam::'):
                return False, "올바른 Role ARN 형식이 아닙니다"
        elif self.connection_type == 'access_key':
            if not self.access_key_id:
                return False, "Access Key ID가 필요합니다"
            if not self.secret_access_key:
                return False, "Secret Access Key가 필요합니다"
            if not self.access_key_id.startswith('AKIA'):
                return False, "Access Key ID는 'AKIA'로 시작해야 합니다"
        
        return True, ""
    
    @classmethod
    def load_all(cls) -> List['AWSAccount']:
        """모든 계정 로드 (mainHub 호환)"""
        accounts = []
        accounts_file = current_app.config['ACCOUNTS_FILE']
        
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            account_data = json.loads(line.strip())
                            accounts.append(cls(account_data))
            except Exception as e:
                current_app.logger.error(f"계정 로드 오류: {e}")
        
        # 중복 제거 (account_id + cloud_name 조합으로)
        seen = set()
        unique_accounts = []
        for account in accounts:
            key = f"{account.account_id}_{account.cloud_name}"
            if key not in seen:
                seen.add(key)
                unique_accounts.append(account)
        
        return unique_accounts
    
    @classmethod
    def find_by_id(cls, account_id: str) -> Optional['AWSAccount']:
        """계정 ID로 검색"""
        accounts = cls.load_all()
        for account in accounts:
            if account.account_id == account_id:
                return account
        return None
    
    @classmethod
    def find_by_id_and_name(cls, account_id: str, cloud_name: str) -> Optional['AWSAccount']:
        """계정 ID와 클라우드 이름으로 검색"""
        accounts = cls.load_all()
        for account in accounts:
            if account.account_id == account_id and account.cloud_name == cloud_name:
                return account
        return None
    
    @classmethod
    def get_statistics(cls) -> Dict:
        """계정 통계 정보 반환"""
        accounts = cls.load_all()
        total_accounts = len(accounts)
        active_accounts = len([acc for acc in accounts if acc.status == 'active'])
        role_based = len([acc for acc in accounts if acc.is_role_based])
        key_based = len([acc for acc in accounts if acc.is_access_key_based])
        
        return {
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'role_based': role_based,
            'key_based': key_based
        }
    
    def save(self):
        """계정 저장 (mainHub 호환)"""
        accounts_file = current_app.config['ACCOUNTS_FILE']
        
        # 기존 계정들 로드
        existing_accounts = []
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing_accounts.append(json.loads(line.strip()))
        
        # 중복 제거 (account_id + cloud_name 기준)
        key = f"{self.account_id}_{self.cloud_name}"
        existing_accounts = [
            acc for acc in existing_accounts 
            if f"{acc.get('account_id', '')}_{acc.get('cloud_name', '')}" != key
        ]
        
        # 생성 시간 업데이트
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        
        # 새 계정 추가
        existing_accounts.append(self.to_dict())
        
        # 파일에 저장 (mainHub와 동일한 형식)
        os.makedirs(os.path.dirname(accounts_file), exist_ok=True)
        with open(accounts_file, 'w', encoding='utf-8') as f:
            for account in existing_accounts:
                f.write(json.dumps(account, ensure_ascii=False) + '\n')
    
    def delete(self):
        """계정 삭제"""
        accounts_file = current_app.config['ACCOUNTS_FILE']
        
        # 기존 계정들 로드
        existing_accounts = []
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing_accounts.append(json.loads(line.strip()))
        
        # 현재 계정 제거
        key = f"{self.account_id}_{self.cloud_name}"
        existing_accounts = [
            acc for acc in existing_accounts 
            if f"{acc.get('account_id', '')}_{acc.get('cloud_name', '')}" != key
        ]
        
        # 파일에 저장
        with open(accounts_file, 'w', encoding='utf-8') as f:
            for account in existing_accounts:
                f.write(json.dumps(account, ensure_ascii=False) + '\n')

    @classmethod
    def delete_by_account_id(cls, account_id: str) -> bool:
        """계정 ID로 계정 삭제"""
        accounts_file = current_app.config['ACCOUNTS_FILE']
        
        if not os.path.exists(accounts_file):
            return False
        
        # 기존 계정들 로드
        existing_accounts = []
        found = False
        
        with open(accounts_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    account_data = json.loads(line.strip())
                    if account_data.get('account_id') != account_id:
                        existing_accounts.append(account_data)
                    else:
                        found = True
        
        if not found:
            return False
        
        # 파일에 저장
        with open(accounts_file, 'w', encoding='utf-8') as f:
            for account in existing_accounts:
                f.write(json.dumps(account, ensure_ascii=False) + '\n')
        
        return True