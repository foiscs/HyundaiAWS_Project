"""
SSH 연결 설정
환경별로 다른 SSH 접속 정보를 관리
"""

import os

class SSHConfig:
    """SSH 연결 설정 관리"""
    
    # 환경 감지: 메인허브 인스턴스인지 로컬인지 확인
    @staticmethod
    def get_environment():
        """현재 실행 환경 확인"""
        # 서버 환경은 /home/ec2-user/HyundaiAWS_Project 디렉토리가 있을 것으로 가정
        if os.path.exists('/home/ec2-user/HyundaiAWS_Project'):
            return 'server'
        # 메인허브 인스턴스는 /opt/splunk 디렉토리가 있을 것으로 가정
        elif os.path.exists('/opt/splunk'):
            return 'mainhub'
        else:
            return 'local'
    
    @staticmethod
    def get_splunk_forwarder_config():
        """환경별 Splunk Forwarder 연결 설정"""
        env = SSHConfig.get_environment()
        
        if env == 'server':
            # 서버 환경에서는 퍼블릭 IP와 서버 내 키 사용
            return {
                'host': '3.35.197.218',
                'user': 'ec2-user',
                'key_path': '/home/ec2-user/HyundaiAWS_Project/walb-flask/SplunkEc2.pem',
                'script_path': './create_kinesis_service.sh'
            }
        elif env == 'mainhub':
            # 메인허브 인스턴스에서는 프라이빗 IP 사용
            # TODO: 실제 splunk-forwarder 인스턴스의 프라이빗 IP로 변경 필요
            return {
                'host': '10.0.1.100',  # splunk-forwarder 프라이빗 IP로 변경
                'user': 'ec2-user',
                'key_path': '/home/ec2-user/HyundaiAWS_Project/walb-flask/SplunkEc2.pem',
                'script_path': './create_kinesis_service.sh'
            }
        else:
            # 로컬 개발 환경에서는 퍼블릭 IP 사용
            return {
                'host': '3.35.197.218',
                'user': 'ec2-user', 
                'key_path': 'C:\\Users\\User\\SplunkEc2.pem',  # Windows 키 경로
                'script_path': './create_kinesis_service.sh'
            }
    
    @staticmethod
    def get_ssh_command_base(config):
        """SSH 기본 명령어 구성"""
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10"
        ]
        
        if config['key_path']:
            ssh_cmd.extend(["-i", config['key_path']])
            
        ssh_cmd.append(f"{config['user']}@{config['host']}")
        return ssh_cmd