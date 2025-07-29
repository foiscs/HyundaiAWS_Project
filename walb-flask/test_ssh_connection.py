"""
SSH 연결 테스트 스크립트
splunk-forwarder 인스턴스와의 연결을 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.kinesis_service import KinesisServiceManager
from app.config.ssh_config import SSHConfig

def test_ssh_connection():
    """SSH 연결 테스트"""
    print("=== SSH 연결 테스트 ===")
    
    # 현재 환경 확인
    env = SSHConfig.get_environment()
    print(f"현재 환경: {env}")
    
    # SSH 설정 확인
    ssh_config = SSHConfig.get_splunk_forwarder_config()
    print(f"SSH 설정:")
    print(f"  - Host: {ssh_config['host']}")
    print(f"  - User: {ssh_config['user']}")
    print(f"  - Key Path: {ssh_config['key_path']}")
    print(f"  - Script Path: {ssh_config['script_path']}")
    print()
    
    # KinesisServiceManager 초기화
    try:
        manager = KinesisServiceManager()
        print("✅ KinesisServiceManager 초기화 성공")
    except Exception as e:
        print(f"❌ KinesisServiceManager 초기화 실패: {e}")
        return
    
    # 기본 SSH 연결 테스트 
    print("\n=== 기본 SSH 연결 테스트 ===")
    try:
        success, stdout, stderr = manager._run_ssh_command("echo 'SSH 연결 테스트 성공'", timeout=30)
        
        if success:
            print("✅ SSH 연결 성공")
            print(f"응답: {stdout.strip()}")
        else:
            print("❌ SSH 연결 실패")
            print(f"에러: {stderr}")
            
    except Exception as e:
        print(f"❌ SSH 연결 중 예외 발생: {e}")
    
    # create_kinesis_service.sh 스크립트 존재 확인
    print("\n=== 스크립트 파일 확인 ===")
    try:
        success, stdout, stderr = manager._run_ssh_command(f"ls -la {manager.script_path}", timeout=30)
        
        if success:
            print("✅ create_kinesis_service.sh 스크립트 존재 확인")
            print(f"파일 정보:\n{stdout}")
        else:
            print("❌ create_kinesis_service.sh 스크립트를 찾을 수 없음")
            print(f"에러: {stderr}")
            
    except Exception as e:
        print(f"❌ 스크립트 확인 중 예외 발생: {e}")

    # 스크립트 실행 권한 확인
    print("\n=== 스크립트 실행 권한 확인 ===")
    try:
        success, stdout, stderr = manager._run_ssh_command(f"bash {manager.script_path}", timeout=30)
        
        if "사용법:" in stdout or "Usage:" in stdout:
            print("✅ 스크립트 실행 권한 확인 (사용법 출력)")
            print("스크립트 사용법:")
            print(stdout)
        else:
            print("⚠️ 스크립트 응답이 예상과 다름")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            
    except Exception as e:
        print(f"❌ 스크립트 실행 권한 확인 중 예외 발생: {e}")

if __name__ == "__main__":
    test_ssh_connection()