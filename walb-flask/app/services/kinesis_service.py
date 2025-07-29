"""
Kinesis 서비스 관리 모듈
splunk-forwarder 인스턴스의 create_kinesis_service.sh 스크립트를 통해
계정별 Kinesis 로그 수집 서비스를 원격으로 관리
"""

import subprocess
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from app.models.account import AWSAccount
from app.config.ssh_config import SSHConfig

logger = logging.getLogger(__name__)

class KinesisServiceManager:
    """Kinesis 로그 수집 서비스 관리"""
    
    def __init__(self):
        # 환경별 SSH 설정 자동 로드
        ssh_config = SSHConfig.get_splunk_forwarder_config()
        self.splunk_forwarder_host = ssh_config['host']
        self.ssh_user = ssh_config['user'] 
        self.ssh_key_path = ssh_config['key_path']
        self.script_path = ssh_config['script_path']
        
        logger.info(f"SSH Config loaded - Host: {self.splunk_forwarder_host}, User: {self.ssh_user}")
        
    def _run_ssh_command(self, command: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """SSH를 통해 원격 명령어 실행"""
        # SSH 설정 사용
        config = {
            'host': self.splunk_forwarder_host,
            'user': self.ssh_user,
            'key_path': self.ssh_key_path
        }
        
        ssh_cmd = SSHConfig.get_ssh_command_base(config)
        ssh_cmd.append(command)
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"SSH command timeout: {command}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"SSH command error: {e}")
            return False, "", str(e)
    
    def create_kinesis_service(self, account: AWSAccount) -> Dict[str, Any]:
        """계정에 대한 Kinesis 서비스 생성"""
        try:
            # 스크립트 실행 명령어 구성 (sudo 권한 필요)
            if account.connection_type == 'role':
                command = f"sudo bash {self.script_path} role {account.account_id} {account.role_arn} {account.primary_region}"
            else:  # access key 방식
                command = f"sudo bash {self.script_path} accesskey {account.account_id} {account.access_key_id} {account.secret_access_key} {account.primary_region}"
            
            logger.info(f"Creating Kinesis service for account {account.account_id}")
            success, stdout, stderr = self._run_ssh_command(command)
            
            if success:
                logger.info(f"Kinesis service created successfully for {account.account_id}")
                return {
                    "success": True,
                    "message": f"Kinesis 서비스가 성공적으로 생성되었습니다 (계정: {account.account_id})",
                    "output": stdout,
                    "service_name": f"kinesis-splunk-forwarder-{account.account_id}"
                }
            else:
                logger.error(f"Failed to create Kinesis service for {account.account_id}: {stderr}")
                return {
                    "success": False,
                    "message": f"Kinesis 서비스 생성 실패: {stderr}",
                    "output": stdout,
                    "error": stderr
                }
                
        except Exception as e:
            logger.error(f"Error creating Kinesis service: {e}")
            return {
                "success": False,
                "message": f"서비스 생성 중 오류 발생: {str(e)}",
                "error": str(e)
            }
    
    def start_kinesis_service(self, account_id: str) -> Dict[str, Any]:
        """Kinesis 서비스 시작"""
        service_name = f"kinesis-splunk-forwarder-{account_id}"
        
        try:
            # systemctl enable 후 start
            enable_cmd = f"sudo systemctl enable {service_name}"
            start_cmd = f"sudo systemctl start {service_name}"
            
            # 서비스 활성화
            success, stdout, stderr = self._run_ssh_command(enable_cmd)
            if not success:
                return {
                    "success": False,
                    "message": f"서비스 활성화 실패: {stderr}",
                    "error": stderr
                }
            
            # 서비스 시작
            success, stdout, stderr = self._run_ssh_command(start_cmd)
            if success:
                logger.info(f"Kinesis service started for account {account_id}")
                return {
                    "success": True,
                    "message": f"Kinesis 서비스가 시작되었습니다 (계정: {account_id})",
                    "output": stdout
                }
            else:
                logger.error(f"Failed to start Kinesis service for {account_id}: {stderr}")
                return {
                    "success": False,
                    "message": f"서비스 시작 실패: {stderr}",
                    "error": stderr
                }
                
        except Exception as e:
            logger.error(f"Error starting Kinesis service: {e}")
            return {
                "success": False,
                "message": f"서비스 시작 중 오류 발생: {str(e)}",
                "error": str(e)
            }
    
    def stop_kinesis_service(self, account_id: str) -> Dict[str, Any]:
        """Kinesis 서비스 중지"""
        service_name = f"kinesis-splunk-forwarder-{account_id}"
        
        try:
            command = f"sudo systemctl stop {service_name}"
            success, stdout, stderr = self._run_ssh_command(command)
            
            if success:
                logger.info(f"Kinesis service stopped for account {account_id}")
                return {
                    "success": True,
                    "message": f"Kinesis 서비스가 중지되었습니다 (계정: {account_id})",
                    "output": stdout
                }
            else:
                logger.error(f"Failed to stop Kinesis service for {account_id}: {stderr}")
                return {
                    "success": False,
                    "message": f"서비스 중지 실패: {stderr}",
                    "error": stderr
                }
                
        except Exception as e:
            logger.error(f"Error stopping Kinesis service: {e}")
            return {
                "success": False,
                "message": f"서비스 중지 중 오류 발생: {str(e)}",
                "error": str(e)
            }
    
    def get_service_status(self, account_id: str) -> Dict[str, Any]:
        """Kinesis 서비스 상태 확인"""
        service_name = f"kinesis-splunk-forwarder-{account_id}"
        
        try:
            # systemctl status 명령어 실행
            command = f"sudo systemctl status {service_name} --no-pager"
            success, stdout, stderr = self._run_ssh_command(command, timeout=30)
            
            # 서비스 상태 파싱
            status_info = {
                "service_name": service_name,
                "exists": False,
                "active": False,
                "enabled": False,
                "running": False,
                "last_output": "",
                "error": None
            }
            
            if success or "could not be found" not in stderr:
                status_info["exists"] = True
                
                # Active 상태 확인
                if "Active: active" in stdout:
                    status_info["active"] = True
                    status_info["running"] = True
                elif "Active: inactive" in stdout:
                    status_info["active"] = False
                elif "Active: failed" in stdout:
                    status_info["active"] = False
                    status_info["error"] = "Service failed"
                
                # Enabled 상태 확인
                if "Loaded:" in stdout and "enabled" in stdout:
                    status_info["enabled"] = True
                
                status_info["last_output"] = stdout
            else:
                status_info["error"] = "Service not found"
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return {
                "service_name": service_name,
                "exists": False,
                "active": False,
                "enabled": False,
                "running": False,
                "error": str(e)
            }
    
    def get_service_logs(self, account_id: str, lines: int = 50) -> Dict[str, Any]:
        """Kinesis 서비스 로그 조회"""
        service_name = f"kinesis-splunk-forwarder-{account_id}"
        
        try:
            command = f"sudo journalctl -u {service_name} -n {lines} --no-pager"
            success, stdout, stderr = self._run_ssh_command(command, timeout=30)
            
            if success:
                return {
                    "success": True,
                    "logs": stdout,
                    "lines_count": len(stdout.split('\n')) if stdout else 0
                }
            else:
                return {
                    "success": False,
                    "error": stderr,
                    "logs": ""
                }
                
        except Exception as e:
            logger.error(f"Error getting service logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": ""
            }
    
    def list_all_kinesis_services(self) -> List[Dict[str, Any]]:
        """모든 Kinesis 서비스 목록 조회"""
        try:
            command = "sudo systemctl list-units --type=service | grep 'kinesis-splunk-forwarder'"
            success, stdout, stderr = self._run_ssh_command(command, timeout=30)
            
            services = []
            if success and stdout:
                for line in stdout.strip().split('\n'):
                    if 'kinesis-splunk-forwarder' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            service_name = parts[0]
                            account_id = service_name.replace('kinesis-splunk-forwarder-', '').replace('.service', '')
                            
                            services.append({
                                'account_id': account_id,
                                'service_name': service_name,
                                'status': parts[2],  # active/inactive
                                'running': parts[3]  # running/dead
                            })
            
            return services
            
        except Exception as e:
            logger.error(f"Error listing Kinesis services: {e}")
            return []
    
    def remove_kinesis_service(self, account_id: str) -> Dict[str, Any]:
        """Kinesis 서비스 완전 제거"""
        service_name = f"kinesis-splunk-forwarder-{account_id}"
        
        try:
            # 서비스 중지
            stop_result = self.stop_kinesis_service(account_id)
            
            # 서비스 비활성화
            disable_cmd = f"sudo systemctl disable {service_name}"
            success, stdout, stderr = self._run_ssh_command(disable_cmd)
            
            # 서비스 파일 삭제
            remove_cmd = f"sudo rm -f /etc/systemd/system/{service_name}.service"
            success, stdout, stderr = self._run_ssh_command(remove_cmd)
            
            # systemd 데몬 재로드
            reload_cmd = "sudo systemctl daemon-reload"
            success, stdout, stderr = self._run_ssh_command(reload_cmd)
            
            if success:
                logger.info(f"Kinesis service removed for account {account_id}")
                return {
                    "success": True,
                    "message": f"Kinesis 서비스가 완전히 제거되었습니다 (계정: {account_id})"
                }
            else:
                return {
                    "success": False,
                    "message": f"서비스 제거 중 일부 오류 발생: {stderr}"
                }
                
        except Exception as e:
            logger.error(f"Error removing Kinesis service: {e}")
            return {
                "success": False,
                "message": f"서비스 제거 중 오류 발생: {str(e)}",
                "error": str(e)
            }