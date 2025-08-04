"""
Flask 애플리케이션 설정 파일
"""
import os

class Config:
    # Flask 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'walb-dev-secret-key-2024'
    
    # 디버그 모드
    DEBUG = True
    
    # 데이터 파일 경로
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    ACCOUNTS_FILE = os.path.join(DATA_DIR, 'registered_accounts.json')
    DIAGNOSIS_HISTORY_FILE = os.path.join(DATA_DIR, 'diagnosis_history.json')
    
    # AWS 설정
    AWS_DEFAULT_REGION = 'ap-northeast-2'
    
    # WALB 서비스 설정 - EC2 인스턴스 Role 사용으로 Access Key 불필요
    WALB_SERVICE_ACCOUNT_ID = "253157413163"  # EC2-KinesisForwarder-Role이 속한 계정
    # Access Key 설정 제거 - EC2 Role 자동 사용
    
    # 개발 모드 설정
    DEVELOPMENT_MODE = os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true'
    
    # 진단 설정
    DIAGNOSIS_TIMEOUT = 60  # 초 (30→60으로 증가)
    MAX_CONCURRENT_DIAGNOSIS = 5
    
    # 로깅 설정
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY')

# 설정 딕셔너리
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}