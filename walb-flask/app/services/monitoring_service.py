"""
모니터링 서비스 클래스
AWS 계정의 모니터링 상태를 관리합니다.
SSH 연결을 통한 서비스 관리 기능을 포함합니다.
"""

import boto3
import logging
import subprocess
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
from app.models.account import AWSAccount

logger = logging.getLogger(__name__)

class MonitoringService:
    """AWS 리소스 모니터링을 담당하는 서비스 클래스"""
    
    def __init__(self):
        self.logger = logger
    
    def create_aws_session(self, account: AWSAccount) -> boto3.Session:
        """AWS 세션 생성"""
        try:
            if account.connection_type == 'role':
                # Cross-Account Role 방식
                temp_session = boto3.Session(
                    aws_access_key_id=account.access_key_id,
                    aws_secret_access_key=account.secret_access_key,
                    region_name=account.primary_region
                )
                
                sts_client = temp_session.client('sts')
                assumed_role = sts_client.assume_role(
                    RoleArn=account.role_arn,
                    RoleSessionName='monitoring-session'
                )
                
                credentials = assumed_role['Credentials']
                return boto3.Session(
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken'],
                    region_name=account.primary_region
                )
            else:
                # Access Key 방식
                return boto3.Session(
                    aws_access_key_id=account.access_key_id,
                    aws_secret_access_key=account.secret_access_key,
                    region_name=account.primary_region
                )
                
        except Exception as e:
            logger.error(f"Failed to create AWS session: {e}")
            raise
    
    def create_service_account_via_ssh(self, instance_ip: str, ssh_key_path: str, 
                                     service_name: str, account_id: str) -> Dict:
        """SSH를 통해 원격 인스턴스에서 서비스 계정 생성"""
        try:
            # SSH 키 권한 설정
            os.chmod(ssh_key_path, 0o600)
            
            # 서비스 계정 생성 스크립트
            create_script = f"""
#!/bin/bash
set -e

echo "=== 서비스 계정 생성 시작 ==="

# 서비스 사용자 생성
sudo useradd -r -s /bin/bash -m -d /opt/{service_name} {service_name} 2>/dev/null || true

# 서비스 디렉토리 생성
sudo mkdir -p /opt/{service_name}/{{logs,config,bin}}
sudo chown -R {service_name}:{service_name} /opt/{service_name}

# AWS CLI 설정 디렉토리 생성
sudo -u {service_name} mkdir -p /opt/{service_name}/.aws

# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/{service_name}.service > /dev/null << 'EOF'
[Unit]
Description={service_name.title()} Monitoring Service
After=network.target

[Service]
Type=simple
User={service_name}
WorkingDirectory=/opt/{service_name}
ExecStart=/opt/{service_name}/bin/start.sh
Restart=always
RestartSec=10
Environment=HOME=/opt/{service_name}
Environment=AWS_CONFIG_FILE=/opt/{service_name}/.aws/config
Environment=AWS_SHARED_CREDENTIALS_FILE=/opt/{service_name}/.aws/credentials

[Install]
WantedBy=multi-user.target
EOF

# systemd 데몬 리로드
sudo systemctl daemon-reload

echo "=== 서비스 계정 생성 완료 ==="
echo "Service User: {service_name}"
echo "Service Directory: /opt/{service_name}"
echo "Service File: /etc/systemd/system/{service_name}.service"
"""
            
            # SSH로 스크립트 실행
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                create_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'서비스 계정 {service_name} 생성 완료',
                    'service_user': service_name,
                    'service_directory': f'/opt/{service_name}',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': f'서비스 계정 생성 실패: {result.stderr}',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'SSH 연결 시간 초과',
                'error': 'Connection timeout'
            }
        except Exception as e:
            logger.error(f"Error creating service account via SSH: {e}")
            return {
                'success': False,
                'message': f'서비스 계정 생성 중 오류: {str(e)}',
                'error': str(e)
            }
    
    def create_service_role_arn(self, account: AWSAccount, service_name: str) -> Dict:
        """서비스용 IAM Role과 ARN 생성"""
        try:
            session = self.create_aws_session(account)
            iam_client = session.client('iam')
            
            role_name = f'{service_name}-monitoring-role'
            policy_name = f'{service_name}-monitoring-policy'
            
            # Trust Policy 정의
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Permission Policy 정의
            permission_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:DescribeLogGroups",
                            "logs:DescribeLogStreams",
                            "cloudtrail:DescribeTrails",
                            "cloudtrail:GetTrailStatus",
                            "guardduty:ListDetectors",
                            "guardduty:GetDetector",
                            "guardduty:GetFindings",
                            "kinesis:PutRecord",
                            "kinesis:PutRecords",
                            "kinesis:DescribeStream"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            try:
                # IAM Role 생성
                role_response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f'Monitoring service role for {service_name}'
                )
                
                role_arn = role_response['Role']['Arn']
                
                # Policy 생성
                policy_response = iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(permission_policy),
                    Description=f'Monitoring permissions for {service_name}'
                )
                
                policy_arn = policy_response['Policy']['Arn']
                
                # Policy를 Role에 연결
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                
                # Instance Profile 생성 및 Role 연결
                instance_profile_name = f'{service_name}-instance-profile'
                
                try:
                    iam_client.create_instance_profile(
                        InstanceProfileName=instance_profile_name
                    )
                    
                    iam_client.add_role_to_instance_profile(
                        InstanceProfileName=instance_profile_name,
                        RoleName=role_name
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'EntityAlreadyExists':
                        raise
                
                return {
                    'success': True,
                    'message': f'서비스 Role ARN 생성 완료',
                    'role_arn': role_arn,
                    'policy_arn': policy_arn,
                    'instance_profile': instance_profile_name,
                    'role_name': role_name
                }
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'EntityAlreadyExists':
                    # 기존 Role 정보 반환
                    existing_role = iam_client.get_role(RoleName=role_name)
                    return {
                        'success': True,
                        'message': f'기존 서비스 Role 사용',
                        'role_arn': existing_role['Role']['Arn'],
                        'role_name': role_name,
                        'existed': True
                    }
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Error creating service role ARN: {e}")
            return {
                'success': False,
                'message': f'서비스 Role ARN 생성 실패: {str(e)}',
                'error': str(e)
            }
    
    def remove_kinesis_service(self, instance_ip: str, ssh_key_path: str, 
                                 account_id: str) -> Dict:
        """SSH를 통해 기존 Kinesis 서비스 완전 제거"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            service_name = f"kinesis-splunk-forwarder-{account_id}"
            
            # 서비스 제거 스크립트
            remove_script = f"""
#!/bin/bash
set -e

echo "=== Kinesis Service Removal Started ==="

# 서비스 중지 및 비활성화
sudo systemctl stop {service_name} 2>/dev/null || echo "Service not running"
sudo systemctl disable {service_name} 2>/dev/null || echo "Service not enabled"

# 서비스 파일 제거
if [ -f "/etc/systemd/system/{service_name}.service" ]; then
    sudo rm -f "/etc/systemd/system/{service_name}.service"
    echo "✅ Service file removed: /etc/systemd/system/{service_name}.service"
else
    echo "⚠️ Service file not found"
fi

# Python 스크립트 제거
if [ -f "/opt/kinesis_splunk_forwarder.py" ]; then
    sudo rm -f "/opt/kinesis_splunk_forwarder.py"
    echo "✅ Python script removed: /opt/kinesis_splunk_forwarder.py"
else
    echo "⚠️ Python script not found"
fi

# 로그 디렉토리는 데이터 보존을 위해 제거하지 않음
if [ -d "/var/log/splunk/{account_id}" ]; then
    echo "📁 Log directory preserved: /var/log/splunk/{account_id}"
    echo "   (Contains existing log data - not removed)"
else
    echo "📁 Log directory not found"
fi

# systemd 데몬 리로드
sudo systemctl daemon-reload

echo "=== Kinesis Service Removal Completed ==="
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no', 
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                remove_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Kinesis 서비스 제거 완료 (로그 데이터는 보존됨)',
                    'output': result.stdout,
                    'service_name': service_name,
                    'logs_preserved': True
                }
            else:
                return {
                    'success': False,
                    'message': f'Kinesis 서비스 제거 실패: {result.stderr}',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error removing Kinesis service: {e}")
            return {
                'success': False,
                'message': f'서비스 제거 중 오류: {str(e)}',
                'error': str(e)
            }

    def execute_kinesis_service_script(self, instance_ip: str, ssh_key_path: str, 
                                     account: 'AWSAccount', reinstall: bool = False) -> Dict:
        """SSH를 통해 실제 create_kinesis_service.sh 스크립트 실행"""
        try:
            # SSH 키 권한 설정
            os.chmod(ssh_key_path, 0o600)
            
            # 재설치인 경우 기존 서비스 먼저 제거
            if reinstall:
                logger.info(f"Reinstall mode: removing existing service for account {account.account_id}")
                remove_result = self.remove_kinesis_service(instance_ip, ssh_key_path, account.account_id)
                if not remove_result['success']:
                    logger.warning(f"Service removal failed, but continuing with installation: {remove_result.get('message')}")
            
            # 계정 타입에 따른 스크립트 명령어 생성
            if account.connection_type == 'role':
                script_command = f"sudo ./create_kinesis_service.sh role {account.account_id} {account.role_arn} {account.primary_region}"
            else:
                script_command = f"sudo ./create_kinesis_service.sh accesskey {account.account_id} {account.access_key_id} {account.secret_access_key} {account.primary_region}"
            
            # SSH로 스크립트 실행
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                script_command
            ]
            
            logger.info(f"Executing SSH command: {' '.join(ssh_command[:-1])} [SCRIPT_COMMAND]")
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=120  # 2분 타임아웃
            )
            
            # 결과 파싱 및 반환
            service_name = f"kinesis-splunk-forwarder-{account.account_id}"
            
            if result.returncode == 0 or "서비스 파일 생성 완료" in result.stdout:
                # 성공 또는 부분 성공
                return {
                    'success': True,
                    'message': f'Kinesis 서비스 스크립트 실행 완료 (실제 실행)',
                    'script_command': script_command.replace('sudo ', ''),
                    'actual_output': result.stdout + result.stderr,
                    'service_details': {
                        'service_name': service_name,
                        'service_file': f'/etc/systemd/system/{service_name}.service',
                        'python_script': '/opt/kinesis_splunk_forwarder.py',
                        'status': 'created/running',
                        'streams_connected': ['cloudtrail-stream'],
                        'log_destination': f'/var/log/splunk/{account.account_id}/cloudtrail.log'
                    },
                    'ssh_info': {
                        'host': instance_ip,
                        'user': 'ec2-user',
                        'key': ssh_key_path.split('\\')[-1],  # 파일명만 표시
                        'executed_command': script_command,
                        'return_code': result.returncode
                    }
                }
            else:
                # 실패
                return {
                    'success': False,
                    'message': f'Kinesis 서비스 스크립트 실행 실패',
                    'error': result.stderr or result.stdout,
                    'return_code': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'SSH 연결 또는 스크립트 실행 시간 초과',
                'error': 'Timeout after 2 minutes'
            }
        except Exception as e:
            logger.error(f"Error executing kinesis script via SSH: {e}")
            return {
                'success': False,
                'message': f'SSH 실행 중 오류: {str(e)}',
                'error': str(e)
            }

    def check_linux_service_status(self, instance_ip: str, ssh_key_path: str, 
                                 service_name: str) -> Dict:
        """SSH를 통해 리눅스 서비스 상태 확인"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            # 서비스 상태 확인 스크립트
            status_script = f"""
#!/bin/bash

echo "=== 서비스 상태 확인 ==="

# systemd 서비스 상태
echo "--- Systemd Status ---"
sudo systemctl status {service_name} --no-pager || echo "Service not found"

echo ""
echo "--- Service Enabled Status ---"
sudo systemctl is-enabled {service_name} 2>/dev/null || echo "not-enabled"

echo ""
echo "--- Service Active Status ---"
sudo systemctl is-active {service_name} 2>/dev/null || echo "inactive"

echo ""
echo "--- Recent Logs ---"
sudo journalctl -u {service_name} --no-pager -n 10 2>/dev/null || echo "No logs available"

echo ""
echo "--- Process Check ---"
ps aux | grep {service_name} | grep -v grep || echo "No process found"
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                status_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                
                # 상태 파싱
                is_active = 'active' in result.stdout
                is_enabled = 'enabled' in result.stdout
                has_process = 'No process found' not in result.stdout
                
                return {
                    'success': True,
                    'service_name': service_name,
                    'is_active': is_active,
                    'is_enabled': is_enabled,
                    'has_process': has_process,
                    'status': 'running' if is_active and has_process else 'stopped',
                    'raw_output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': f'서비스 상태 확인 실패',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error checking Linux service status: {e}")
            return {
                'success': False,
                'message': f'서비스 상태 확인 중 오류: {str(e)}',
                'error': str(e)
            }
    
    def check_cloudwatch_status(self, account: AWSAccount) -> Dict:
        """CloudWatch 로그 그룹 상태 확인"""
        try:
            session = self.create_aws_session(account)
            logs_client = session.client('logs')
            
            # 주요 로그 그룹들 확인
            log_groups = [
                '/aws/lambda/security-function',
                '/aws/apigateway/access-logs',
                '/aws/vpc/flowlogs',
                '/aws/cloudtrail'
            ]
            
            status = {
                'service': 'CloudWatch',
                'active': False,
                'log_groups': [],
                'total_size': 0,
                'last_activity': None
            }
            
            for log_group in log_groups:
                try:
                    response = logs_client.describe_log_groups(
                        logGroupNamePrefix=log_group,
                        limit=1
                    )
                    
                    if response['logGroups']:
                        group = response['logGroups'][0]
                        status['log_groups'].append({
                            'name': group['logGroupName'],
                            'size': group.get('storedBytes', 0),
                            'retention': group.get('retentionInDays', 'Never expire'),
                            'creation_time': group.get('creationTime')
                        })
                        status['total_size'] += group.get('storedBytes', 0)
                        status['active'] = True
                        
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        logger.warning(f"Error checking log group {log_group}: {e}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking CloudWatch status: {e}")
            return {
                'service': 'CloudWatch', 
                'active': False, 
                'error': str(e)
            }
    
    def check_cloudtrail_status(self, account: AWSAccount) -> Dict:
        """CloudTrail 상태 확인"""
        try:
            session = self.create_aws_session(account)
            cloudtrail_client = session.client('cloudtrail')
            
            # 활성 CloudTrail 조회
            response = cloudtrail_client.describe_trails()
            trails = response.get('trailList', [])
            
            status = {
                'service': 'CloudTrail',
                'active': False,
                'trails': [],
                'logging_enabled': 0,
                'total_trails': len(trails)
            }
            
            for trail in trails:
                trail_status = cloudtrail_client.get_trail_status(
                    Name=trail['TrailARN']
                )
                
                trail_info = {
                    'name': trail['Name'],
                    'is_logging': trail_status['IsLogging'],
                    'last_delivery': trail_status.get('LatestDeliveryTime'),
                    's3_bucket': trail.get('S3BucketName'),
                    'is_multi_region': trail.get('IsMultiRegionTrail', False)
                }
                
                status['trails'].append(trail_info)
                if trail_status['IsLogging']:
                    status['logging_enabled'] += 1
                    status['active'] = True
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking CloudTrail status: {e}")
            return {
                'service': 'CloudTrail', 
                'active': False, 
                'error': str(e)
            }
    
    def check_guardduty_status(self, account: AWSAccount) -> Dict:
        """GuardDuty 상태 확인"""
        try:
            session = self.create_aws_session(account)
            guardduty_client = session.client('guardduty')
            
            # GuardDuty 탐지기 목록 조회
            response = guardduty_client.list_detectors()
            detector_ids = response.get('DetectorIds', [])
            
            status = {
                'service': 'GuardDuty',
                'active': False,
                'detectors': [],
                'finding_counts': {'High': 0, 'Medium': 0, 'Low': 0}
            }
            
            for detector_id in detector_ids:
                detector_response = guardduty_client.get_detector(
                    DetectorId=detector_id
                )
                
                detector_status = detector_response.get('Status', 'DISABLED')
                
                # 최근 findings 개수 확인
                try:
                    findings_response = guardduty_client.get_findings_statistics(
                        DetectorId=detector_id,
                        FindingStatisticTypes=['COUNT_BY_SEVERITY']
                    )
                    findings_stats = findings_response.get('FindingStatistics', {})
                except Exception as e:
                    logger.warning(f"Error getting GuardDuty findings statistics: {e}")
                    findings_stats = {}
                
                detector_info = {
                    'id': detector_id,
                    'status': detector_status,
                    'service_role': detector_response.get('ServiceRole'),
                    'data_sources': detector_response.get('DataSources', {}),
                    'findings_stats': findings_stats
                }
                
                status['detectors'].append(detector_info)
                if detector_status == 'ENABLED':
                    status['active'] = True
                    
                    # Findings 통계 집계
                    count_by_severity = findings_stats.get('CountBySeverity', [])
                    if isinstance(count_by_severity, list):
                        for stat in count_by_severity:
                            severity = stat.get('Severity')
                            count = stat.get('Count', 0)
                            if severity in status['finding_counts']:
                                status['finding_counts'][severity] += count
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking GuardDuty status: {e}")
            return {
                'service': 'GuardDuty', 
                'active': False, 
                'error': str(e)
            }
    
    def check_log_files_status(self, instance_ip: str, ssh_key_path: str, 
                             account_id: str) -> Dict:
        """SSH를 통해 실제 로그 파일들의 수집 상태 확인"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            log_base_path = f"/var/log/splunk/{account_id}"
            log_files = {
                'cloudtrail': f'{log_base_path}/cloudtrail.log',
                'guardduty': f'{log_base_path}/guardduty.log',
                'security-hub': f'{log_base_path}/security-hub.log'
            }
            
            # 로그 파일 상태 확인 스크립트
            check_script = f"""
#!/bin/bash
echo "=== Log Files Status Check ==="
cd {log_base_path} 2>/dev/null || {{ echo "Directory not found: {log_base_path}"; exit 1; }}

for log_file in cloudtrail.log guardduty.log security-hub.log; do
    echo "--- $log_file ---"
    if [ -f "$log_file" ]; then
        # 파일 크기 (바이트)
        size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
        echo "SIZE:$size"
        
        # 최근 수정 시간 (Unix timestamp)
        mtime=$(stat -c%Y "$log_file" 2>/dev/null || echo "0")
        echo "MTIME:$mtime"
        
        # 라인 수
        lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
        echo "LINES:$lines"
        
        # 마지막 3줄 (로그 내용 샘플)
        echo "LAST_LINES:"
        tail -n 3 "$log_file" 2>/dev/null || echo "No content"
        echo "END_LAST_LINES"
        
        echo "STATUS:EXISTS"
    else
        echo "SIZE:0"
        echo "MTIME:0"
        echo "LINES:0"
        echo "LAST_LINES:"
        echo "File not found"
        echo "END_LAST_LINES"
        echo "STATUS:NOT_FOUND"
    fi
    echo ""
done
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                check_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # 인코딩 에러 무시
                timeout=60
            )
            
            if result.returncode == 0:
                # 결과 파싱
                return self._parse_log_status_output(result.stdout, log_files)
            else:
                return {
                    'success': False,
                    'message': '로그 파일 상태 확인 실패',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error checking log files status: {e}")
            return {
                'success': False,
                'message': f'로그 파일 상태 확인 중 오류: {str(e)}',
                'error': str(e)
            }
    
    def _parse_log_status_output(self, output: str, log_files: Dict) -> Dict:
        """로그 상태 체크 출력 파싱"""
        from datetime import datetime, timezone
        import re
        
        # 계정 ID 안전하게 추출
        account_id = 'unknown'
        try:
            log_files_str = str(log_files.values())
            if '/' in log_files_str:
                path_parts = log_files_str.split('/')
                if len(path_parts) >= 2:
                    # /var/log/splunk/253157413163/cloudtrail.log 형태에서 계정 ID 추출
                    for part in path_parts:
                        if part.isdigit() and len(part) == 12:  # AWS 계정 ID는 12자리 숫자
                            account_id = part
                            break
        except Exception:
            account_id = 'unknown'
        
        result = {
            'success': True,
            'account_id': account_id,
            'log_files': {},
            'overall_health': 0,
            'total_size': 0,
            'last_checked': datetime.now().isoformat()
        }
        
        # 각 로그 파일별로 파싱
        current_file = None
        current_data = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('--- ') and line.endswith(' ---'):
                # 새로운 파일 섹션 시작
                if current_file and current_data:
                    result['log_files'][current_file] = current_data
                
                current_file = line[4:-4]  # '--- cloudtrail.log ---' -> 'cloudtrail.log'
                file_key = current_file.replace('.log', '')
                current_data = {
                    'file_name': current_file,
                    'file_path': log_files.get(file_key, f'/var/log/splunk/{result["account_id"]}/{current_file}'),
                    'exists': False,
                    'size': 0,
                    'size_mb': 0.0,
                    'lines': 0,
                    'last_modified': None,
                    'last_modified_ago': 'Unknown',
                    'is_recent': False,
                    'sample_lines': [],
                    'health_score': 0
                }
                
            elif line.startswith('SIZE:'):
                current_data['size'] = int(line[5:])
                current_data['size_mb'] = round(current_data['size'] / 1024 / 1024, 2)
                result['total_size'] += current_data['size']
                
            elif line.startswith('MTIME:'):
                mtime = int(line[6:])
                if mtime > 0:
                    current_data['last_modified'] = datetime.fromtimestamp(mtime).isoformat()
                    # 최근 업데이트 여부 계산 (10분 이내면 최근)
                    minutes_ago = (datetime.now().timestamp() - mtime) / 60
                    current_data['last_modified_ago'] = self._format_time_ago(minutes_ago)
                    current_data['is_recent'] = minutes_ago <= 10
                    
            elif line.startswith('LINES:'):
                current_data['lines'] = int(line[6:])
                
            elif line.startswith('STATUS:'):
                current_data['exists'] = line[7:] == 'EXISTS'
                
            elif line == 'LAST_LINES:':
                # 다음 라인들부터 END_LAST_LINES까지 수집
                current_data['sample_lines'] = []
                
            elif line == 'END_LAST_LINES':
                pass  # 샘플 라인 수집 종료
                
            elif current_data and 'sample_lines' in current_data and line != 'LAST_LINES:':
                if len(current_data['sample_lines']) < 3:
                    current_data['sample_lines'].append(line)
        
        # 마지막 파일 데이터 추가
        if current_file and current_data:
            result['log_files'][current_file] = current_data
        
        # 건강도 점수 계산
        total_health = 0
        file_count = 0
        
        for file_key, file_data in result['log_files'].items():
            health = 0
            if file_data['exists']:
                health += 40  # 파일 존재
                if file_data['size'] > 0:
                    health += 30  # 내용 있음
                if file_data['is_recent']:
                    health += 30  # 최근 업데이트됨
            
            file_data['health_score'] = health
            total_health += health
            file_count += 1
        
        result['overall_health'] = round(total_health / max(file_count, 1))
        result['total_size_mb'] = round(result['total_size'] / 1024 / 1024, 2)
        
        return result
    
    def _format_time_ago(self, minutes: float) -> str:
        """시간 경과를 사용자 친화적 형태로 변환"""
        if minutes < 1:
            return "방금 전"
        elif minutes < 60:
            return f"{int(minutes)}분 전"
        elif minutes < 1440:  # 24시간
            hours = int(minutes / 60)
            return f"{hours}시간 전"
        else:
            days = int(minutes / 1440)
            return f"{days}일 전"
    
    def check_kinesis_service_exists(self, instance_ip: str, ssh_key_path: str, 
                                   account_id: str) -> Dict:
        """SSH를 통해 Kinesis 서비스가 이미 존재하는지 확인"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            service_name = f"kinesis-splunk-forwarder-{account_id}"
            
            # Kinesis 서비스 존재 여부 확인 스크립트
            check_script = f"""
#!/bin/bash
echo "=== Kinesis Service Check ==="

# 서비스 파일 존재 확인
SERVICE_FILE="/etc/systemd/system/{service_name}.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "SERVICE_FILE_EXISTS:true"
    echo "SERVICE_FILE_PATH:$SERVICE_FILE"
else
    echo "SERVICE_FILE_EXISTS:false"
fi

# 서비스 상태 확인
SERVICE_STATUS=$(sudo systemctl is-active {service_name} 2>/dev/null || echo "inactive")
echo "SERVICE_STATUS:$SERVICE_STATUS"

SERVICE_ENABLED=$(sudo systemctl is-enabled {service_name} 2>/dev/null || echo "disabled")
echo "SERVICE_ENABLED:$SERVICE_ENABLED"

# Python 스크립트 파일 확인
PYTHON_SCRIPT="/opt/kinesis_splunk_forwarder.py"
if [ -f "$PYTHON_SCRIPT" ]; then
    echo "PYTHON_SCRIPT_EXISTS:true"
    echo "PYTHON_SCRIPT_PATH:$PYTHON_SCRIPT"
else
    echo "PYTHON_SCRIPT_EXISTS:false"
fi

# 프로세스 확인
PROCESS_COUNT=$(ps aux | grep kinesis_splunk_forwarder | grep -v grep | wc -l)
echo "PROCESS_COUNT:$PROCESS_COUNT"

# 로그 디렉토리 확인
LOG_DIR="/var/log/splunk/{account_id}"
if [ -d "$LOG_DIR" ]; then
    echo "LOG_DIR_EXISTS:true"
    echo "LOG_DIR_PATH:$LOG_DIR"
    
    # 로그 파일들 확인
    for log_file in cloudtrail.log guardduty.log security-hub.log; do
        if [ -f "$LOG_DIR/$log_file" ]; then
            size=$(stat -c%s "$LOG_DIR/$log_file" 2>/dev/null || echo "0")
            echo "LOG_FILE_${{log_file%.*}}_EXISTS:true"
            echo "LOG_FILE_${{log_file%.*}}_SIZE:$size"
        else
            echo "LOG_FILE_${{log_file%.*}}_EXISTS:false"
            echo "LOG_FILE_${{log_file%.*}}_SIZE:0"
        fi
    done
else
    echo "LOG_DIR_EXISTS:false"
fi

# 최근 로그 확인 (서비스가 활성화되어 있는 경우)
if [ "$SERVICE_STATUS" == "active" ]; then
    echo "RECENT_LOGS:"
    sudo journalctl -u {service_name} --no-pager -n 5 2>/dev/null | tail -n 5 || echo "No recent logs"
    echo "END_RECENT_LOGS"
fi
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                check_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return self._parse_kinesis_service_check(result.stdout, service_name, account_id)
            else:
                return {
                    'success': False,
                    'message': 'Kinesis 서비스 상태 확인 실패',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error checking Kinesis service exists: {e}")
            return {
                'success': False,
                'message': f'Kinesis 서비스 확인 중 오류: {str(e)}',
                'error': str(e)
            }
    
    def _parse_kinesis_service_check(self, output: str, service_name: str, account_id: str) -> Dict:
        """Kinesis 서비스 체크 출력 파싱"""
        result = {
            'success': True,
            'service_name': service_name,
            'account_id': account_id,
            'service_exists': False,
            'service_running': False,
            'service_enabled': False,
            'has_process': False,
            'python_script_exists': False,
            'log_directory_exists': False,
            'log_files': {},
            'recent_logs': [],
            'installation_complete': False,
            'status_summary': 'not_installed'
        }
        
        lines = output.split('\n')
        in_recent_logs = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SERVICE_FILE_EXISTS:'):
                result['service_exists'] = line.split(':')[1] == 'true'
            elif line.startswith('SERVICE_STATUS:'):
                status = line.split(':')[1]
                result['service_running'] = status == 'active'
            elif line.startswith('SERVICE_ENABLED:'):
                enabled = line.split(':')[1]
                result['service_enabled'] = enabled == 'enabled'
            elif line.startswith('PYTHON_SCRIPT_EXISTS:'):
                result['python_script_exists'] = line.split(':')[1] == 'true'
            elif line.startswith('PROCESS_COUNT:'):
                count = int(line.split(':')[1])
                result['has_process'] = count > 0
            elif line.startswith('LOG_DIR_EXISTS:'):
                result['log_directory_exists'] = line.split(':')[1] == 'true'
            elif line.startswith('LOG_FILE_') and '_EXISTS:' in line:
                # LOG_FILE_cloudtrail_EXISTS:true
                parts = line.split('_')
                if len(parts) >= 3:
                    log_type = parts[2]  # cloudtrail, guardduty, security-hub 등
                    exists = line.split(':')[1] == 'true'
                    if log_type not in result['log_files']:
                        result['log_files'][log_type] = {}
                    result['log_files'][log_type]['exists'] = exists
            elif line.startswith('LOG_FILE_') and '_SIZE:' in line:
                # LOG_FILE_cloudtrail_SIZE:12345
                parts = line.split('_')
                if len(parts) >= 3:
                    log_type = parts[2]
                    size = int(line.split(':')[1])
                    if log_type not in result['log_files']:
                        result['log_files'][log_type] = {}
                    result['log_files'][log_type]['size'] = size
                    result['log_files'][log_type]['size_mb'] = round(size / 1024 / 1024, 2)
            elif line == 'RECENT_LOGS:':
                in_recent_logs = True
            elif line == 'END_RECENT_LOGS':
                in_recent_logs = False
            elif in_recent_logs and line:
                result['recent_logs'].append(line)
        
        # 설치 완료 여부 판단
        result['installation_complete'] = (
            result['service_exists'] and 
            result['python_script_exists'] and 
            result['log_directory_exists']
        )
        
        # 상태 요약 결정
        if result['installation_complete']:
            if result['service_running']:
                result['status_summary'] = 'running'
            elif result['service_enabled']:
                result['status_summary'] = 'installed_stopped'
            else:
                result['status_summary'] = 'installed_disabled'
        else:
            result['status_summary'] = 'not_installed'
        
        return result

    def get_log_file_preview(self, instance_ip: str, ssh_key_path: str, 
                           account_id: str, log_type: str, lines: int = 50) -> Dict:
        """SSH를 통해 특정 로그 파일의 최근 내용 가져오기"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            log_file_path = f"/var/log/splunk/{account_id}/{log_type}.log"
            
            # 로그 파일 미리보기 스크립트
            preview_script = f"""
#!/bin/bash
echo "=== Log File Preview: {log_type}.log ==="
if [ -f "{log_file_path}" ]; then
    echo "FILE_EXISTS:true"
    echo "FILE_SIZE:$(stat -c%s '{log_file_path}')"
    echo "LAST_MODIFIED:$(stat -c%Y '{log_file_path}')"
    echo "TOTAL_LINES:$(wc -l < '{log_file_path}')"
    echo "PREVIEW_CONTENT:"
    tail -n {lines} "{log_file_path}"
    echo "END_PREVIEW_CONTENT"
else
    echo "FILE_EXISTS:false"
    echo "ERROR:File not found: {log_file_path}"
fi
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                preview_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return self._parse_log_preview_output(result.stdout, log_type, account_id)
            else:
                return {
                    'success': False,
                    'message': '로그 파일 미리보기 실패',
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error getting log file preview: {e}")
            return {
                'success': False,
                'message': f'로그 파일 미리보기 중 오류: {str(e)}',
                'error': str(e)
            }
    
    def _parse_log_preview_output(self, output: str, log_type: str, account_id: str) -> Dict:
        """로그 미리보기 출력 파싱"""
        from datetime import datetime
        
        result = {
            'success': True,
            'log_type': log_type,
            'account_id': account_id,
            'file_exists': False,
            'file_size': 0,
            'total_lines': 0,
            'last_modified': None,
            'content': [],
            'formatted_content': ''
        }
        
        lines = output.split('\n')
        in_content = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('FILE_EXISTS:'):
                result['file_exists'] = line.split(':')[1] == 'true'
            elif line.startswith('FILE_SIZE:'):
                result['file_size'] = int(line.split(':')[1])
            elif line.startswith('LAST_MODIFIED:'):
                timestamp = int(line.split(':')[1])
                result['last_modified'] = datetime.fromtimestamp(timestamp).isoformat()
            elif line.startswith('TOTAL_LINES:'):
                result['total_lines'] = int(line.split(':')[1])
            elif line == 'PREVIEW_CONTENT:':
                in_content = True
            elif line == 'END_PREVIEW_CONTENT':
                in_content = False
            elif in_content:
                result['content'].append(line)
        
        # 내용을 하나의 문자열로 합치기
        result['formatted_content'] = '\n'.join(result['content'])
        
        return result

    def _convert_datetime_to_string(self, obj):
        """재귀적으로 datetime 객체를 문자열로 변환"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_datetime_to_string(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_string(item) for item in obj]
        else:
            return obj

    def get_comprehensive_monitoring_status(self, account: AWSAccount) -> Dict:
        """종합 모니터링 상태 확인"""
        try:
            cloudwatch_status = self.check_cloudwatch_status(account)
            cloudtrail_status = self.check_cloudtrail_status(account)
            guardduty_status = self.check_guardduty_status(account)
            
            # 전체 상태 요약
            overall_status = {
                'account_id': account.account_id,
                'account_name': account.cloud_name,
                'region': account.primary_region,
                'services': {
                    'cloudwatch': cloudwatch_status,
                    'cloudtrail': cloudtrail_status,
                    'guardduty': guardduty_status
                },
                'overall_health': 'healthy' if all([
                    cloudwatch_status.get('active', False),
                    cloudtrail_status.get('active', False),
                    guardduty_status.get('active', False)
                ]) else 'degraded',
                'last_checked': datetime.now().isoformat()
            }
            
            # 모든 datetime 객체를 문자열로 변환
            overall_status = self._convert_datetime_to_string(overall_status)
            
            return overall_status
            
        except Exception as e:
            logger.error(f"Error getting comprehensive monitoring status: {e}")
            return {
                'account_id': account.account_id,
                'error': str(e),
                'overall_health': 'error',
                'last_checked': datetime.now().isoformat()
            }

    def manage_kinesis_service(self, instance_ip: str, ssh_key_path: str, 
                             account_id: str, action: str) -> Dict:
        """SSH를 통해 Kinesis 서비스 관리 (start/stop/restart)"""
        try:
            os.chmod(ssh_key_path, 0o600)
            
            service_name = f"kinesis-splunk-forwarder-{account_id}"
            
            # 액션에 따른 명령어 결정
            action_commands = {
                'start': f'sudo systemctl start {service_name}',
                'stop': f'sudo systemctl stop {service_name}',
                'restart': f'sudo systemctl restart {service_name}'
            }
            
            if action not in action_commands:
                return {
                    'success': False,
                    'message': f'지원하지 않는 액션입니다: {action}',
                    'error': f'Invalid action: {action}'
                }
            
            # 서비스 관리 스크립트
            manage_script = f"""
#!/bin/bash
set -e

echo "=== Kinesis Service Management: {action.upper()} ==="

# 현재 상태 확인
echo "--- Current Status ---"
sudo systemctl is-active {service_name} 2>/dev/null || echo "inactive"

# 액션 실행
echo "--- Executing {action.upper()} ---"
{action_commands[action]}

# 실행 후 상태 확인
echo "--- New Status ---"
sudo systemctl is-active {service_name} 2>/dev/null || echo "inactive"

# 상세 상태 정보
echo "--- Service Details ---"
sudo systemctl status {service_name} --no-pager -l || echo "Service status unavailable"

echo "=== Service {action.upper()} Completed ==="
"""
            
            ssh_command = [
                'ssh', '-i', ssh_key_path,
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ec2-user@{instance_ip}',
                manage_script
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 결과 파싱
            success_indicators = {
                'start': ['active', 'started'],
                'stop': ['inactive', 'stopped'],
                'restart': ['active', 'restarted']
            }
            
            output_lower = result.stdout.lower()
            is_success = any(indicator in output_lower for indicator in success_indicators[action])
            
            if result.returncode == 0 or is_success:
                return {
                    'success': True,
                    'message': f'Kinesis 서비스 {action} 완료',
                    'action': action,
                    'service_name': service_name,
                    'output': result.stdout,
                    'return_code': result.returncode
                }
            else:
                return {
                    'success': False,
                    'message': f'Kinesis 서비스 {action} 실패',
                    'error': result.stderr or result.stdout,
                    'return_code': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': f'서비스 {action} 시간 초과',
                'error': 'SSH connection timeout'
            }
        except Exception as e:
            logger.error(f"Error managing Kinesis service ({action}): {e}")
            return {
                'success': False,
                'message': f'서비스 {action} 중 오류: {str(e)}',
                'error': str(e)
            }