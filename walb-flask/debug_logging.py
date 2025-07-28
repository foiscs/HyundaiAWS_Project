"""
Flask 컨텍스트에서 로깅 테스트
"""
import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app import create_app

app = create_app()

with app.app_context():
    from app.utils.diagnosis_logger import diagnosis_logger
    
    print("=== 로깅 시스템 테스트 ===")
    
    # 로그 디렉토리 생성 확인
    log_dir = "logs/diagnosis"
    os.makedirs(log_dir, exist_ok=True)
    print(f"로그 디렉토리 생성: {os.path.exists(log_dir)}")
    
    # 테스트 로깅
    session_id = diagnosis_logger.start_session("TestAccount", "batch")
    print(f"세션 시작: {session_id}")
    
    diagnosis_logger.log_diagnosis_start("1.1", "사용자 계정 관리")
    diagnosis_logger.log_diagnosis_result("1.1", "사용자 계정 관리", {
        'status': 'success',
        'result': {
            'has_issues': True,
            'risk_level': 'high',
            'details': {'test': 'data'}
        }
    })
    
    diagnosis_logger.log_session_summary(41, 30, 11)
    log_path = diagnosis_logger.get_session_log_path()
    diagnosis_logger.end_session()
    
    print(f"로그 파일 경로: {log_path}")
    if log_path:
        print(f"파일 존재: {os.path.exists(log_path)}")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"파일 크기: {len(content)} bytes")
                print("=== 로그 내용 ===")
                print(content[:500])  # 처음 500자만 출력
    
    print("\n=== 로그 목록 조회 테스트 ===")
    recent_logs = diagnosis_logger.get_recent_logs(limit=5)
    print(f"최근 로그 수: {len(recent_logs)}")
    for log in recent_logs:
        print(f"- {log['filename']} ({log['size']} bytes)")