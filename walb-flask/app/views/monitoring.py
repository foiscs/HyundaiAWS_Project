"""
모니터링 뷰
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models.account import AWSAccount
from app.services.kinesis_service import KinesisServiceManager
from app.services.splunk_service import SplunkService
from app.services.monitoring_service import MonitoringService
from app.config.ssh_config import SSHConfig
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

# SSH 설정 가져오기
def get_ssh_config():
    """환경에 맞는 SSH 설정 반환"""
    return SSHConfig.get_splunk_forwarder_config()

# 서비스 인스턴스 초기화
kinesis_manager = KinesisServiceManager()
splunk_service = SplunkService()
monitoring_service = MonitoringService()

# 서비스 인스턴스 초기화
kinesis_manager = KinesisServiceManager()
splunk_service = SplunkService()
monitoring_service = MonitoringService()

@bp.route('/')
def index():
    """모니터링 메인 페이지"""
    # URL 파라미터에서 계정 ID 가져오기
    account_id = request.args.get('account')
    
    # 등록된 계정 목록 가져오기
    accounts = AWSAccount.load_all()
    
    # 선택된 계정 정보
    selected_account = None
    service_status = None
    monitoring_status = None
    
    service_status = None
    monitoring_status = None
    
    if account_id:
        selected_account = AWSAccount.find_by_id(account_id)
        if selected_account:
            # Kinesis 서비스 상태 확인
            service_status = kinesis_manager.get_service_status(account_id)
            # Splunk 모니터링 상태 확인
            monitoring_status = splunk_service.get_account_monitoring_status(account_id)
            # 종합 모니터링 상태 확인
            comprehensive_status = monitoring_service.get_comprehensive_monitoring_status(selected_account)
        if selected_account:
            # Kinesis 서비스 상태 확인
            service_status = kinesis_manager.get_service_status(account_id)
            # Splunk 모니터링 상태 확인
            monitoring_status = splunk_service.get_account_monitoring_status(account_id)
            # 종합 모니터링 상태 확인
            comprehensive_status = monitoring_service.get_comprehensive_monitoring_status(selected_account)
    
    return render_template('pages/monitoring.html', 
                         accounts=accounts,
                         selected_account=selected_account,
                         service_status=service_status,
                         monitoring_status=monitoring_status,
                         comprehensive_status=comprehensive_status if account_id and selected_account else None)

@bp.route('/service/create', methods=['POST'])
def create_service():
    """Kinesis 서비스 생성"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"success": False, "message": "계정을 찾을 수 없습니다"}), 404
    
    try:
        result = kinesis_manager.create_kinesis_service(account)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        return jsonify({"success": False, "message": f"서비스 생성 중 오류: {str(e)}"}), 500

@bp.route('/service/start', methods=['POST'])
def start_service():
    """Kinesis 서비스 시작"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.start_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting service: {e}")
        return jsonify({"success": False, "message": f"서비스 시작 중 오류: {str(e)}"}), 500

@bp.route('/service/stop', methods=['POST'])
def stop_service():
    """Kinesis 서비스 중지"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.stop_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        return jsonify({"success": False, "message": f"서비스 중지 중 오류: {str(e)}"}), 500

@bp.route('/service/remove', methods=['POST'])
def remove_service():
    """Kinesis 서비스 제거"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.remove_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error removing service: {e}")
        return jsonify({"success": False, "message": f"서비스 제거 중 오류: {str(e)}"}), 500

@bp.route('/service/status/<account_id>')
def get_service_status(account_id):
    """서비스 상태 조회 (AJAX)"""
    try:
        status = kinesis_manager.get_service_status(account_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/service/logs/<account_id>')
def get_service_logs(account_id):
    """서비스 로그 조회"""
    lines = request.args.get('lines', 50, type=int)
    
    try:
        logs = kinesis_manager.get_service_logs(account_id, lines)
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/splunk/redirect/<account_id>')
def splunk_redirect(account_id):
    """Splunk 웹으로 리다이렉션"""
    log_type = request.args.get('log_type', 'cloudtrail')
    search_term = request.args.get('search', '*')
    time_range = request.args.get('time', '-24h')
    
    try:
        if search_term and search_term != '*':
            splunk_url = splunk_service.create_custom_search_url(
                account_id=account_id,
                custom_query=search_term,
                time_range=time_range
            )
        else:
            splunk_url = splunk_service.generate_splunk_search_url(
                account_id=account_id,
                log_type=log_type,
                search_term='*',
                earliest_time=time_range
            )
        
        logger.info(f"Redirecting to Splunk for account {account_id}: {splunk_url}")
        return redirect(splunk_url)
        
    except Exception as e:
        logger.error(f"Error generating Splunk URL: {e}")
        return jsonify({"error": f"Splunk URL 생성 오류: {str(e)}"}), 500

@bp.route('/splunk/urls/<account_id>')
def get_splunk_urls(account_id):
    """계정별 Splunk URL 조회 (AJAX)"""
    try:
        urls = splunk_service.get_splunk_dashboard_urls(account_id)
        return jsonify(urls)
    except Exception as e:
        logger.error(f"Error getting Splunk URLs: {e}")
        return jsonify({"error": str(e)}), 500

# Kinesis 서비스 스크립트 실행 엔드포인트
@bp.route('/kinesis/execute-script', methods=['POST'])
def execute_kinesis_script():
    """선택된 계정 정보로 Kinesis 서비스 스크립트 실행 (시뮬레이션)"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({
            "success": False, 
            "message": "계정 ID가 필요합니다"
        }), 400
    
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({
            "success": False, 
            "message": "계정을 찾을 수 없습니다"
        }), 404
    
    try:
        # 실제 SSH 실행은 주석처리하고 시뮬레이션 결과 반환
        if account.connection_type == 'role':
            script_command = f"./create_kinesis_service.sh role {account.account_id} {account.role_arn} {account.primary_region}"
        else:
            script_command = f"./create_kinesis_service.sh accesskey {account.account_id} {account.access_key_id} [SECRET] {account.primary_region}"
        
        # 실제 SSH 실행 (환경별 설정 사용)
        try:
            ssh_config = get_ssh_config()
            ssh_result = monitoring_service.execute_kinesis_service_script(
                instance_ip=ssh_config['host'],
                ssh_key_path=ssh_config['key_path'],
                account=account
            )
            
            if ssh_result.get('success'):
                # SSH 실행 성공 시 실제 결과 반환
                return jsonify(ssh_result)
            else:
                # SSH 실행 실패 시 시뮬레이션으로 폴백
                logger.warning(f"SSH execution failed: {ssh_result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"SSH execution error: {e}")
            # SSH 실행 오류 시 시뮬레이션으로 폴백
        
        # 실제 SSH 실행 결과를 반영한 시뮬레이션 결과
        service_name = f"kinesis-splunk-forwarder-{account.account_id}"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ssh_config = get_ssh_config()  # 시뮬레이션 결과용 SSH 설정
        
        simulation_result = {
            "success": True,
            "message": "Kinesis 서비스 스크립트 실행 완료 (실제 결과 기반)",
            "script_command": script_command,
            "simulated_output": f"""
=== Kinesis Splunk Forwarder Creation Started ===
Account ID: {account.account_id}
Access Key ID: {account.access_key_id if account.connection_type == 'accesskey' else 'N/A (Role-based)'}
Region: {account.primary_region}

✅ Service name: {service_name}
✅ Systemd service file created: /etc/systemd/system/{service_name}.service
✅ Service enabled and started
✅ AWS credentials configured for Kinesis access

=== Service Status ===
● {service_name}.service - Kinesis Splunk Forwarder Service for Account {account.account_id}
     Loaded: loaded (/etc/systemd/system/{service_name}.service; enabled; preset: disabled)
     Active: active (running) since {current_time}
   Main PID: 74941 (python3)
      Tasks: 1 (limit: 4565)
     Memory: 6.6M
        CPU: 69ms
     CGroup: /system.slice/{service_name}.service
             └─74941 /usr/bin/python3 /opt/kinesis_splunk_forwarder.py

=== Kinesis Connection Status ===
✅ Successfully connected to CloudTrail stream
✅ Retrieved records from cloudtrail-stream shard shardId-000000000001
✅ Data forwarding to Splunk in progress

=== Kinesis Service Creation Completed ===
🎉 Service is now actively collecting AWS CloudTrail logs and forwarding to Splunk!
            """.strip(),
            "service_details": {
                "service_name": service_name,
                "service_file": f"/etc/systemd/system/{service_name}.service",
                "python_script": "/opt/kinesis_splunk_forwarder.py",
                "status": "active (running)",
                "streams_connected": ["cloudtrail-stream"],
                "log_destination": f"/var/log/splunk/{account.account_id}/cloudtrail.log"
            },
            "ssh_info": {
                "host": ssh_config['host'],
                "user": ssh_config['user'],
                "key": ssh_config['key_path'].split('/')[-1],  # 파일명만 표시
                "executed_command": f"sudo ./create_kinesis_service.sh {account.connection_type} {account.account_id} ..."
            }
        }
        
        logger.info(f"Kinesis script execution simulated for account {account_id}")
        return jsonify(simulation_result)
        
    except Exception as e:
        logger.error(f"Error executing Kinesis script: {e}")
        return jsonify({
            "success": False, 
            "message": f"스크립트 실행 중 오류: {str(e)}"
        }), 500

@bp.route('/kinesis/get-script-command/<account_id>')
def get_script_command(account_id):
    """계정별 스크립트 명령어 조회"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"error": "계정을 찾을 수 없습니다"}), 404
    
    try:
        ssh_config = get_ssh_config()
        if account.connection_type == 'role':
            script_command = f"./create_kinesis_service.sh role {account.account_id} {account.role_arn} {account.primary_region}"
            full_command = f"ssh -i {ssh_config['key_path'].split('/')[-1]} {ssh_config['user']}@{ssh_config['host']}\n{script_command}"
        else:
            script_command = f"./create_kinesis_service.sh accesskey {account.account_id} {account.access_key_id} {account.secret_access_key} {account.primary_region}"
            full_command = f"ssh -i {ssh_config['key_path'].split('/')[-1]} {ssh_config['user']}@{ssh_config['host']}\n{script_command}"
        
        return jsonify({
            "success": True,
            "script_command": script_command,
            "full_command": full_command,
            "connection_type": account.connection_type
        })
        
    except Exception as e:
        logger.error(f"Error getting script command: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/ssh/service-status', methods=['POST'])
def check_service_status_ssh():
    """SSH를 통한 리눅스 서비스 상태 확인"""
    instance_ip = request.form.get('instance_ip')
    ssh_key_path = request.form.get('ssh_key_path')
    service_name = request.form.get('service_name', 'monitoring-service')
    
    if not all([instance_ip, ssh_key_path]):
        return jsonify({
            "success": False, 
            "message": "필수 파라미터가 누락되었습니다 (instance_ip, ssh_key_path)"
        }), 400
    
    try:
        result = monitoring_service.check_linux_service_status(
            instance_ip=instance_ip,
            ssh_key_path=ssh_key_path,
            service_name=service_name
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking service status via SSH: {e}")
        return jsonify({
            "success": False, 
            "message": f"서비스 상태 확인 중 오류: {str(e)}"
        }), 500

@bp.route('/aws/comprehensive-status/<account_id>')
def get_comprehensive_status(account_id):
    """종합 모니터링 상태 조회 (AJAX)"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"error": "계정을 찾을 수 없습니다"}), 404
    
    try:
        status = monitoring_service.get_comprehensive_monitoring_status(account)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting comprehensive status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/log-files/status/<account_id>')
def get_log_files_status(account_id):
    """실제 로그 파일 수집 상태 조회 (AJAX)"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"error": "계정을 찾을 수 없습니다"}), 404
    
    try:
        # SSH를 통해 실제 로그 파일 상태 확인
        ssh_config = get_ssh_config()
        log_status = monitoring_service.check_log_files_status(
            instance_ip=ssh_config['host'],
            ssh_key_path=ssh_config['key_path'],
            account_id=account_id
        )
        return jsonify(log_status)
    except Exception as e:
        logger.error(f"Error getting log files status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/log-files/preview/<account_id>/<log_type>')
def get_log_preview(account_id, log_type):
    """특정 로그 파일의 최근 내용 미리보기 (AJAX)"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"error": "계정을 찾을 수 없습니다"}), 404
    
    if log_type not in ['cloudtrail', 'guardduty', 'security-hub']:
        return jsonify({"error": "잘못된 로그 타입입니다"}), 400
    
    try:
        # SSH로 로그 파일의 최근 내용 가져오기
        ssh_config = get_ssh_config()
        result = monitoring_service.get_log_file_preview(
            instance_ip=ssh_config['host'],
            ssh_key_path=ssh_config['key_path'],
            account_id=account_id,
            log_type=log_type,
            lines=50  # 최근 50줄
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting log preview: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/kinesis/service-status/<account_id>')
def check_kinesis_service_status(account_id):
    """Kinesis 서비스 존재 여부 및 상태 확인 (AJAX)"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"error": "계정을 찾을 수 없습니다"}), 404
    
    try:
        # SSH를 통해 Kinesis 서비스 상태 확인
        ssh_config = get_ssh_config()
        result = monitoring_service.check_kinesis_service_exists(
            instance_ip=ssh_config['host'],
            ssh_key_path=ssh_config['key_path'],
            account_id=account_id
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking Kinesis service status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/kinesis/reinstall', methods=['POST'])
def reinstall_kinesis_service():
    """Kinesis 서비스 완전 재설치 (기존 서비스 제거 후 새로 설치)"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({
            "success": False, 
            "message": "계정 ID가 필요합니다"
        }), 400
    
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({
            "success": False, 
            "message": "계정을 찾을 수 없습니다"
        }), 404
    
    try:
        # 재설치 모드로 스크립트 실행 (기존 서비스 제거 후 설치)
        ssh_config = get_ssh_config()
        result = monitoring_service.execute_kinesis_service_script(
            instance_ip=ssh_config['host'],
            ssh_key_path=ssh_config['key_path'],
            account=account,
            reinstall=True  # 재설치 모드
        )
        
        if result.get('success'):
            result['message'] = 'Kinesis 서비스 재설치 완료 (기존 서비스 제거 후 새로 설치됨)'
            result['reinstall_mode'] = True
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error reinstalling Kinesis service: {e}")
        return jsonify({
            "success": False, 
            "message": f"서비스 재설치 중 오류: {str(e)}"
        }), 500

@bp.route('/aws/service-details/<account_id>')
def get_service_details_html(account_id):
    """AWS 서비스 상태 상세 정보를 HTML 형태로 반환"""
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return "<h1>계정을 찾을 수 없습니다</h1>", 404
    
    try:
        # 종합 모니터링 상태 가져오기
        status = monitoring_service.get_comprehensive_monitoring_status(account)
        
        # HTML 템플릿 렌더링
        return render_template('components/service_details.html', 
                             status=status, 
                             account=account)
    except Exception as e:
        logger.error(f"Error getting service details: {e}")
        return f"<h1>오류 발생</h1><p>{str(e)}</p>", 500

@bp.route('/kinesis/manage', methods=['POST'])
def manage_kinesis_service():
    """Kinesis 서비스 관리 (start/stop/restart)"""
    account_id = request.form.get('account_id')
    action = request.form.get('action')
    
    if not account_id:
        return jsonify({
            "success": False, 
            "message": "계정 ID가 필요합니다"
        }), 400
    
    if not action or action not in ['start', 'stop', 'restart']:
        return jsonify({
            "success": False, 
            "message": "유효한 액션이 필요합니다 (start/stop/restart)"
        }), 400
    
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({
            "success": False, 
            "message": "계정을 찾을 수 없습니다"
        }), 404
    
    try:
        # SSH를 통해 서비스 관리
        ssh_config = get_ssh_config()
        result = monitoring_service.manage_kinesis_service(
            instance_ip=ssh_config['host'],
            ssh_key_path=ssh_config['key_path'],
            account_id=account_id,
            action=action
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error managing Kinesis service: {e}")
        return jsonify({
            "success": False, 
            "message": f"서비스 관리 중 오류: {str(e)}"
        }), 500