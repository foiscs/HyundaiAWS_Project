#!/usr/bin/env python3
"""
SSH 설정 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'walb-flask'))

from app.config.ssh_config import SSHConfig

print("=== SSH Configuration Test ===")

# 환경 감지 테스트
env = SSHConfig.get_environment()
print(f"Detected environment: {env}")

# 설정 가져오기
config = SSHConfig.get_splunk_forwarder_config()
print(f"SSH Configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")

# 키 파일 존재 여부 확인
print(f"\nSSH Key file exists: {os.path.exists(config['key_path'])}")

if os.path.exists(config['key_path']):
    # 키 파일 권한 확인 (Unix 시스템에서만)
    if hasattr(os, 'stat'):
        import stat
        file_stat = os.stat(config['key_path'])
        permissions = stat.filemode(file_stat.st_mode)
        print(f"Key file permissions: {permissions}")
else:
    print(f"WARNING: SSH key file not found at {config['key_path']}")